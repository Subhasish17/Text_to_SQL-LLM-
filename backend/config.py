import os
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("No API key found. Please set GEMINI_API_KEY in your .env file.")

# Qdrant Memory Settings
COLLECTION_NAME = "schema_vectors"
VECTOR_DIMENSION = 3072  # Updated to match gemini-embedding-2 dimensions

# Data Directory
DATA_DIR = "data/"