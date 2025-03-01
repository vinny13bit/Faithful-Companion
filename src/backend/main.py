import os
import sqlite3
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
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            user_message TEXT NOT NULL,
            ai_response TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY(username) REFERENCES users(username)
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
    """Basic username-password authentication with SQLite storage."""
    username = user_data.get("username")
    password = user_data.get("password")
    
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        if existing_user[0] != password:
            conn.close()
            raise HTTPException(status_code=401, detail="Invalid password")
    else:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
    
    conn.close()
    return {"message": "Login successful", "username": username}

@app.get("/chat-history/{username}")
def get_chat_history(username: str):
    """Retrieve chat history for a specific user from SQLite."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_message, ai_response, timestamp FROM chat_history WHERE username = ? ORDER BY id DESC LIMIT 50", (username,))
    history = [
        {"user": row[0], "ai": row[1], "timestamp": row[2]} for row in cursor.fetchall()
    ]
    conn.close()
    return {"history": history}

@app.post("/chat/{username}")
async def chat_with_ai(username: str, user_input: dict):
    """Mock response while waiting for OpenAI quota reset, stored in SQLite."""
    prompt = user_input.get("prompt")
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    
    response_text = f"Mock response for: {prompt}"
    timestamp = datetime.utcnow().isoformat()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_history (username, user_message, ai_response, timestamp) VALUES (?, ?, ?, ?)", 
                   (username, prompt, response_text, timestamp))
    conn.commit()
    conn.close()
    
    return {"response": response_text}

@app.delete("/clear-chat-history/{username}")
def clear_chat_history(username: str):
    """Clear chat history for a specific user in SQLite."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    return {"message": f"Chat history cleared for {username}"}

# Run server using: uvicorn main:app --reload
