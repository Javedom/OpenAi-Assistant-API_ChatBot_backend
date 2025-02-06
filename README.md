# OpenAi-Assistant-API_v2_backend for a chatbot

This project provides a Flask-based backend that integrates with OpenAI's API to facilitate conversational interactions. Below, you will find instructions on setup, configuration, usage, and further details on how the service manages user conversations and responses.

This backend offers an endpoint (/api/chat) that clients can use to send user messages and receive AI-generated responses. It leverages:

Flask for the web server.
OpenAI Python client (via openai package) for conversation handling.
Flask-CORS for configuring cross-origin resource sharing.
Flask-Limiter for rate limiting requests.

**Features**
Simple Chat Interface: Send user messages to /api/chat and retrieve AI-generated responses.
In-memory Thread Management: Stores thread/session IDs in memory for each user.
Persisted Conversation Logs: Saves all user and AI interactions to a JSON file (conversations.json by default).
Configurable Rate Limiting: Limits how often a user can call the endpoint (default: 5 calls/minute).
CORS Support: Easily restricts or allows specified domains.

**Prerequisites**

Before using this code, ensure you have:
Python 3.7+ (Recommended: Python 3.9+)
pip (Python package manager)

**Setup and Installation**
Clone the repository:
git clone https://github.com/yourusername/chatbot-backend.git
cd chatbot-backend

Install required packages:
pip install -r requirements.txt

Make sure your requirements.txt includes:
Flask
flask-cors
flask-limiter
openai
python-dotenv

Create and configure .env file (See Environment Variables).
Run the application:
python main.py
By default, it listens on port 5000. You can configure the port through the PORT environment variable.

Environment Variables
Your .env file should contain:


OPENAI_API_KEY=<your_openai_api_key>
OPENAI_ASSISTANT_ID=<your_assistant_id>
PORT=5000 (optional: Which port the Flask app should listen on. Defaults to 5000.)


HTTP POST to /api/chat:
{
  "user_id": "user123", 
  "message": "Hello, how are you?"
}

Response:
{
  "answer": "<AI-generated response>"
}
user_id (optional) helps the server track conversation threads. If not provided, it defaults to "anonymous".
message is the user’s text that will be processed by the OpenAI model.

Rate Limiting
This code uses Flask-Limiter to restrict how frequently each client (identified by IP address) can call the API. By default,
5 per minute: Each user can make a maximum of five requests per minute. To adjust this rate:
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["5 per minute"]
)
Change the ["5 per minute"] limit to your desired threshold.

Conversation Logging
User interactions are saved to a JSON file called conversations.json. Each user’s messages and the corresponding AI responses are stored as a list of objects, each containing:
{
  "user": "Hello!",
  "bot": "Hello there! How can I help you today?",
  "timestamp": 1696614303.123
}
Note: For production, consider using a data store (e.g., PostgreSQL, MongoDB) instead of a JSON file for better scalability and reliability.

**Logging and Debugging**
The backend uses the Python logging module to print debug and error messages to the console. Adjust the log level in the code:
logging.basicConfig(level=logging.DEBUG)
Possible levels: DEBUG, INFO, WARNING, ERROR, CRITICAL.

**Extending the Backend**
Model Customization: Modify the OpenAI call to use different models with advanced parameters (like temperature, max_tokens, etc.).
Enhanced Thread Management: Replace in-memory thread storage with a database for persistent session handling.
Asynchronous Processing: Move time-consuming operations into background jobs using tools like Celery or RQ for non-blocking user responses.
