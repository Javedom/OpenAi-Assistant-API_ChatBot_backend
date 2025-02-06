import os
import time
import logging
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import openai
from dotenv import load_dotenv

# Configure logging to output debug statements.
logging.basicConfig(level=logging.DEBUG)

# Load environment variables
load_dotenv()

# OpenAI API Key and Assistant ID
API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")

ALLOWED_DOMAINS = [
    "https://your_domain_here",
    "https://your_domain_here"
]

# Initialize OpenAI Client
client = openai.OpenAI(api_key=API_KEY)

# Initialize Flask app
app = Flask(__name__)

# Apply CORS restrictions
CORS(app, resources={r"/*": {"origins": ALLOWED_DOMAINS}})

# Set up Rate Limiting for api calls (limit per IP)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["5 per minute"]
)

# In-memory storage for chat threads (consider a persistent store for production)
thread_ids = {}
instruction_msg_ids = {}

CONVERSATION_FILE = "conversations.json"

def load_conversations(): #This creates and saves a json file, should be changed to save to a db
    """Load existing conversations from a file or create a new one if empty/corrupt."""
    if not os.path.exists(CONVERSATION_FILE) or os.stat(CONVERSATION_FILE).st_size == 0:
        with open(CONVERSATION_FILE, "w") as file:
            json.dump({}, file)  # Initialize with empty JSON
    try:
        with open(CONVERSATION_FILE, "r") as file:
            return json.load(file)
    except json.JSONDecodeError:
        logging.error("Corrupted JSON file. Resetting conversations.json.")
        with open(CONVERSATION_FILE, "w") as file:
            json.dump({}, file)
        return {}

def save_conversations(conversations):
    """Save conversations to a file."""
    with open(CONVERSATION_FILE, "w") as file:
        json.dump(conversations, file, indent=4)

def log_conversation(user_id, user_message, bot_response):
    """Persist the conversation log."""
    conversations = load_conversations()
    if user_id not in conversations:
        conversations[user_id] = []
    conversations[user_id].append({
        "user": user_message,
        "bot": bot_response,
        "timestamp": time.time()
    })
    save_conversations(conversations)

def extract_assistant_response(msg): #Note: This function might be, for the most parts, redundant
    """
    Attempts to extract the text content from an assistant message.
    Supports different response structures and logs details to aid debugging.
    
    :param msg: The message object (or dict) returned from the OpenAI API.
    :return: Extracted text if found; otherwise, None.
    """
    try:
        # Attempt to obtain the content attribute (object or dict).
        content = getattr(msg, "content", None)
        if content is None and isinstance(msg, dict):
            content = msg.get("content", None)
        logging.debug("Extracted content from message: %s", content)
        if content is None:
            logging.warning("Message has no content field.")
            return None

        # If content is a list, iterate over its parts.
        if isinstance(content, list):
            for part in content:
                logging.debug("Processing part: %s", part)
                # Check if the part has a 'text' field.
                if hasattr(part, "text"):
                    text_field = getattr(part, "text", None)
                elif isinstance(part, dict):
                    text_field = part.get("text", None)
                else:
                    continue
                logging.debug("Found text field: %s", text_field)
                # If text_field is a dict, look for a 'value' key.
                if isinstance(text_field, dict):
                    text_value = text_field.get("value", None)
                    if text_value:
                        return text_value
                # If it's a string, return it directly.
                elif isinstance(text_field, str):
                    return text_field
                # New: If text_field is an object with a 'value' attribute, return that.
                elif hasattr(text_field, "value"):
                    value = getattr(text_field, "value", None)
                    if value:
                        return value

        # If content is already a string, return it.
        elif isinstance(content, str):
            return content

        logging.warning("Unable to extract assistant text from the message: unexpected structure.")
        return None

    except Exception as e:
        logging.error("Error parsing assistant response: %s", e)
        return None

@app.route("/api/chat", methods=["POST"])
@limiter.limit("5 per minute") # Set up Rate Limiting for api calls (limit per IP)
def chat():
    try:
        logging.info("Received request to /api/chat")
        data = request.get_json()
        user_message = data.get("message")
        user_id = data.get("user_id") or "anonymous"

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        if not API_KEY or not ASSISTANT_ID:
            return jsonify({"error": "API key or Assistant ID is missing."}), 500

        # Manage chat threads per user
        if user_id in thread_ids:
            thread_id = thread_ids[user_id]
        else:
            chat_thread = client.beta.threads.create()
            thread_id = chat_thread.id
            thread_ids[user_id] = thread_id

        # Add user message to thread
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )

        # Start OpenAI assistant run
        run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=ASSISTANT_ID)

        # Poll for the run's completion using exponential backoff - Should refactor the blocking retry loop into an asynchronous process or delegate long-running tasks to background workers
        wait_time = 1
        max_attempts = 5
        attempts = 0
        while run.status not in ["completed", "failed", "cancelled"] and attempts < max_attempts:
            time.sleep(wait_time)
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
            logging.debug("Run status: %s", run.status)
            wait_time *= 2
            attempts += 1

        if run.status == "failed":
            logging.error("Assistant run failed.")
            return jsonify({"error": "Assistant run failed"}), 500

        # Retrieve and sort assistant messages
        message_response = client.beta.threads.messages.list(thread_id=thread_id)
        messages = sorted(message_response.data, key=lambda x: x.created_at, reverse=True)
        logging.debug("Retrieved %d messages", len(messages))

        response_text = None
        for msg in messages:
            # Process only assistant messages (skip the initial instruction if applicable)
            if getattr(msg, "role", None) == "assistant" and getattr(msg, "id", None) != instruction_msg_ids.get(user_id):
                logging.debug("Processing assistant message with id: %s", getattr(msg, "id", None))
                response_text = extract_assistant_response(msg)
                logging.debug("Extracted response text: %s", response_text)
                if response_text:
                    break

        if not response_text:
            logging.error("No valid assistant response found. Message objects: %s", messages)
            return jsonify({"error": "No response from Assistant"}), 500

        log_conversation(user_id, user_message, response_text)
        return jsonify({"answer": response_text})

    except openai.OpenAIError as e:
        logging.error("OpenAI API error: %s", e)
        return jsonify({"error": f"OpenAI API error: {str(e)}"}), 500
    except Exception as e:
        logging.error("Unexpected error: %s", e)
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port) #debug=True for testing)
