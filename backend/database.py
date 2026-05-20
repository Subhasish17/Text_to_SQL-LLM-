import os
import sqlite3
import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from google import genai
import backend.config as config

# Initialize pure in-memory databases
qdrant_client = QdrantClient(":memory:")
sql_conn = sqlite3.connect(":memory:", check_same_thread=False)

# New Google GenAI SDK Client
gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)

def find_data_file():
    """Finds the newly uploaded CSV or JSON file in the data directory."""
    if not os.path.exists(config.DATA_DIR):
        os.makedirs(config.DATA_DIR)

    for file in os.listdir(config.DATA_DIR):
        if file.endswith('.csv') or file.endswith('.json'):
            return os.path.join(config.DATA_DIR, file)
            
    raise FileNotFoundError("No .csv or .json file found in the data directory!")

def load_data(file_path):
    if file_path.endswith('.csv'):
        return pd.read_csv(file_path)
    elif file_path.endswith('.json'):
        return pd.read_json(file_path)

def init_databases():
    """Builds the SQLite table and Qdrant vector spaces in RAM."""
    target_file = find_data_file()
    print(f"[*] Processing uploaded file: {target_file}")
    
    df = load_data(target_file)
    
    # Clean column headers for safe SQL syntax
    df.columns = [col.strip().replace(' ', '_').replace('-', '_').lower() for col in df.columns]
    
    # Populate In-Memory SQLite
    table_name = "dataset"
    df.to_sql(table_name, sql_conn, index=False, if_exists="replace")
    print(f"[✓] Data loaded into in-memory SQLite table: '{table_name}'")

    # Populate In-Memory Qdrant
    print("[*] Setting up Qdrant In-Memory Vector Database...")
    qdrant_client.recreate_collection(
        collection_name=config.COLLECTION_NAME,
        vectors_config=VectorParams(size=config.VECTOR_DIMENSION, distance=Distance.COSINE),
    )

    all_columns = df.columns.tolist()
    points = []
    
    print("[*] Generating free semantic vectors via Gemini...")
    for idx, col in enumerate(all_columns):
        desc = f"Column '{col}' in the table '{table_name}'"
        
        # Updated to the new Gemini Embedding 2 model
        result = gemini_client.models.embed_content(
            model="gemini-embedding-2",
            contents=desc
        )
        
        points.append(PointStruct(
            id=idx,
            vector=result.embeddings[0].values,
            payload={"column_name": col, "table_name": table_name}
        ))
        
    qdrant_client.upsert(collection_name=config.COLLECTION_NAME, points=points)
    print(f"[✓] Qdrant setup complete. {len(all_columns)} schema vectors loaded into RAM.")
    
    return table_name, all_columns