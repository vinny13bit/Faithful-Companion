import os
import json
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# CORS (Frontend Communication)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this for security in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Retrieve OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Warning: API key not found. Running in mock mode.")

# Chat history storage
USER_DATA_FOLDER = "user_data"
MESSAGE_LIMIT = 50  # Store only the last 50 messages
USER_CREDENTIALS_FILE = "user_data/user_credentials.json"

# Ensure user data folder exists
os.makedirs(USER_DATA_FOLDER, exist_ok=True)

# Load user credentials
if not os.path.exists(USER_CREDENTIALS_FILE):
    with open(USER_CREDENTIALS_FILE, "w", encoding="utf-8") as file:
        json.dump({}, file)

def get_user_chat_file(username: str):
    return os.path.join(USER_DATA_FOLDER, f"chat_history_{username}.json")

def load_chat_history(username: str):
    """Load chat history for a specific user."""
    chat_file = get_user_chat_file(username)
    if os.path.exists(chat_file):
        with open(chat_file, "r", encoding="utf-8") as file:
            return json.load(file)
    return []

def save_chat_history(username: str, history):
    """Save chat history for a specific user."""
    history = history[-MESSAGE_LIMIT:]  # Keep only the last MESSAGE_LIMIT messages
    chat_file = get_user_chat_file(username)
    with open(chat_file, "w", encoding="utf-8") as file:
        json.dump(history, file, indent=4)

def load_user_credentials():
    """Load stored user credentials."""
    with open(USER_CREDENTIALS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def save_user_credentials(credentials):
    """Save user credentials."""
    with open(USER_CREDENTIALS_FILE, "w", encoding="utf-8") as file:
        json.dump(credentials, file, indent=4)

@app.get("/")
def read_root():
    return {"message": "Faithful Companion API is running"}

@app.get("/check-key")
def check_key():
    """Check if API key is correctly set."""
    return {"API Key Found": OPENAI_API_KEY is not None}

@app.post("/login")
def login(user_data: Dict[str, str]):
    """Basic username-password authentication (not secure yet)."""
    username = user_data.get("username")
    password = user_data.get("password")
    
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    
    credentials = load_user_credentials()
    
    if username in credentials:
        if credentials[username] != password:
            raise HTTPException(status_code=401, detail="Invalid password")
    else:
        credentials[username] = password  # Save new user credentials
        save_user_credentials(credentials)
    
    return {"message": "Login successful", "username": username}

@app.get("/chat-history/{username}")
def get_chat_history(username: str):
    """Retrieve saved chat history for a specific user."""
    return {"history": load_chat_history(username)}

@app.post("/chat/{username}")
async def chat_with_ai(username: str, user_input: dict):
    """Mock response while waiting for OpenAI quota reset."""
    prompt = user_input.get("prompt")
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")

    response = {
        "user": prompt,
        "ai": f"Mock response for: {prompt}",
        "timestamp": datetime.utcnow().isoformat()  # Add timestamp
    }
    history = load_chat_history(username)
    history.append(response)
    save_chat_history(username, history)
    
    return {"response": response["ai"]}

@app.delete("/clear-chat-history/{username}")
def clear_chat_history(username: str):
    """Clear chat history for a specific user."""
    chat_file = get_user_chat_file(username)
    with open(chat_file, "w", encoding="utf-8") as file:
        json.dump([], file, indent=4)
    return {"message": f"Chat history cleared for {username}"}

# Run server using: uvicorn main:app --reload
