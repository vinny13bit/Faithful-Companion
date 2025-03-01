import os
import sqlite3
import bcrypt
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

# Database Setup
DB_PATH = "faithful_companion.db"

def init_db():
    """Initialize the database and create necessary tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(username) REFERENCES users(username)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            user_message TEXT NOT NULL,
            ai_response TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY(conversation_id) REFERENCES conversations(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.get("/")
def read_root():
    return {"message": "Faithful Companion API is running"}

@app.get("/check-key")
def check_key():
    """Check if API key is correctly set."""
    return {"API Key Found": OPENAI_API_KEY is not None}

@app.post("/login")
def login(user_data: Dict[str, str]):
    """Username-password authentication with bcrypt password hashing."""
    username = user_data.get("username")
    password = user_data.get("password").encode('utf-8')
    
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        stored_password = existing_user[0]
        if not bcrypt.checkpw(password, stored_password.encode('utf-8')):
            conn.close()
            raise HTTPException(status_code=401, detail="Invalid password")
    else:
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
    
    conn.close()
    return {"message": "Login successful", "username": username}

@app.post("/start-conversation/{username}")
def start_conversation(username: str):
    """Create a new conversation for the user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.utcnow().isoformat()
    cursor.execute("INSERT INTO conversations (username, created_at) VALUES (?, ?)", (username, timestamp))
    conversation_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"conversation_id": conversation_id}

@app.post("/chat/{conversation_id}")
async def chat_with_ai(conversation_id: int, user_input: dict):
    """Mock response while waiting for OpenAI quota reset, stored in SQLite."""
    prompt = user_input.get("prompt")
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    
    response_text = f"Mock response for: {prompt}"
    timestamp = datetime.utcnow().isoformat()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_history (conversation_id, user_message, ai_response, timestamp) VALUES (?, ?, ?, ?)", 
                   (conversation_id, prompt, response_text, timestamp))
    conn.commit()
    conn.close()
    
    return {"response": response_text}

@app.get("/chat-history/{conversation_id}")
def get_chat_history(conversation_id: int):
    """Retrieve chat history for a specific conversation from SQLite."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_message, ai_response, timestamp FROM chat_history WHERE conversation_id = ? ORDER BY id ASC", (conversation_id,))
    history = [
        {"user": row[0], "ai": row[1], "timestamp": row[2]} for row in cursor.fetchall()
    ]
    conn.close()
    return {"history": history}

@app.delete("/clear-chat-history/{conversation_id}")
def clear_chat_history(conversation_id: int):
    """Clear chat history for a specific conversation in SQLite."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history WHERE conversation_id = ?", (conversation_id,))
    conn.commit()
    conn.close()
    return {"message": f"Chat history cleared for conversation {conversation_id}"}

@app.get("/user-conversations/{username}")
def get_user_conversations(username: str):
    """Retrieve all conversations for a given user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, created_at FROM conversations WHERE username = ? ORDER BY created_at DESC", (username,))
    conversations = [{"id": row[0], "created_at": row[1]} for row in cursor.fetchall()]
    conn.close()
    return {"conversations": conversations}

# Run server using: uvicorn main:app --reload
