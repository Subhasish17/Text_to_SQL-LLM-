import os
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("No API key found. Please set GROQ_API_KEY in your .env file.")

# Data Directory
DATA_DIR = "data/"