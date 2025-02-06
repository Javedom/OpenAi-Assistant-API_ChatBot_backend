# OpenAi-Assistant-API_v2_backend

## Overview
This project provides a Flask-based backend that integrates with OpenAI's API to facilitate conversational interactions. Below are the setup instructions, configuration details, usage guidelines, and insights into how the service manages user conversations and responses.

## Features
- **Simple Chat Interface**: Send user messages to `/api/chat` and retrieve AI-generated responses.
- **In-memory Thread Management**: Stores thread/session IDs in memory for each user.
- **Persisted Conversation Logs**: Saves all user and AI interactions to a JSON file (`conversations.json` by default).
- **Configurable Rate Limiting**: Restricts how often a user can call the endpoint (default: 5 calls/minute).
- **CORS Support**: Easily restricts or allows specified domains.

## Prerequisites
Ensure you have:
- **Python 3.7+** (Recommended: Python 3.9+)
- **pip** (Python package manager)

## Setup and Installation
1. **Clone the repository:**
    ```sh
    git clone https://github.com/javedom/OpenAi-Assistant-API_v2_backend.git
    cd chatbot-backend
    ```
2. **Install required packages:**
    ```sh
    pip install -r requirements.txt
    ```
    Ensure `requirements.txt` includes:
    ```txt
    Flask
    flask-cors
    flask-limiter
    openai
    python-dotenv
    ```
3. **Create and configure `.env` file:** (See [Environment Variables](#environment-variables))
4. **Run the application:**
    ```sh
    python main.py
    ```
    By default, it listens on port 5000. You can configure the port via the `PORT` environment variable.

## Environment Variables
Your `.env` file should contain:
```env
OPENAI_API_KEY=<your_openai_api_key>
OPENAI_ASSISTANT_ID=<your_assistant_id>
PORT=5000  # Optional, defaults to 5000
```

## API Usage
### HTTP POST Request to `/api/chat`
#### Request Body:
```json
{
  "user_id": "user123",
  "message": "Hello, how are you?"
}
```
#### Response:
```json
{
  "answer": "<AI-generated response>"
}
```
- `user_id` *(optional)*: Helps track conversation threads. Defaults to "anonymous" if not provided.
- `message`: The user's text to be processed by the OpenAI model.

## Rate Limiting
This backend uses **Flask-Limiter** to restrict how frequently each client (identified by IP address) can call the API. By default:
- **5 requests per minute**

To adjust this rate, modify the following in `main.py`:
```python
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["5 per minute"]
)
```
Change `"5 per minute"` to your preferred limit.

## Conversation Logging
User interactions are saved to a JSON file (`conversations.json`). Each message is logged as follows:
```json
{
  "user": "Hello!",
  "bot": "Hello there! How can I help you today?",
  "timestamp": 1696614303.123
}
```
**Note:** For production, consider using a database (e.g., PostgreSQL, MongoDB) instead of a JSON file for better scalability and reliability.

## Logging and Debugging
The backend uses the Python **logging** module to print debug and error messages to the console. Adjust the log level in the code:
```python
logging.basicConfig(level=logging.DEBUG)
```
Possible levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

## Extending the Backend
- **Model Customization**: Modify the OpenAI API call to use different models with parameters like `temperature`, `max_tokens`, etc.
- **Enhanced Thread Management**: Replace in-memory storage with a database for persistent session handling.
- **Asynchronous Processing**: Offload time-consuming tasks using **Celery** or **RQ** for non-blocking responses.

## License
This project is licensed under the CC0 License.



