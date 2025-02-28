import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

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

@app.get("/")
def read_root():
    return {"message": "Faithful Companion API is running"}

@app.get("/check-key")
def check_key():
    """Check if API key is correctly set."""
    return {"API Key Found": OPENAI_API_KEY is not None}

@app.post("/chat")
async def chat_with_ai(user_input: dict):
    """Mock response while waiting for OpenAI quota reset."""
    prompt = user_input.get("prompt")
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")

    return {"response": f"Mock response for: {prompt}"}

# Run server using: uvicorn main:app --reload
