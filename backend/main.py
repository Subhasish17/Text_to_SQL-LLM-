from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import pandas as pd
import shutil
import os
import backend.config as config
from backend.database import init_databases, sql_conn
from backend.pipeline import text_to_sql

app = FastAPI(title="Text-to-SQL Dynamic API (Groq Edition)")

# Global variables to hold state after an upload
TABLE_NAME = None
ALL_COLUMNS = None

class QueryRequest(BaseModel):
    prompt: str

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Receives a file, saves it, and builds the in-memory SQLite database instantly."""
    global TABLE_NAME, ALL_COLUMNS
    
    if not os.path.exists(config.DATA_DIR):
        os.makedirs(config.DATA_DIR)
        
    # Clear out old files to ensure a clean database
    for existing_file in os.listdir(config.DATA_DIR):
        os.remove(os.path.join(config.DATA_DIR, existing_file))
        
    # Save the new file
    file_path = os.path.join(config.DATA_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Build SQLite in RAM
    try:
        TABLE_NAME, ALL_COLUMNS = init_databases()
        return {"message": f"Successfully processed {file.filename}", "columns": ALL_COLUMNS}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

@app.post("/api/query")
async def process_query(request: QueryRequest):
    """Executes English queries against the uploaded data using Groq."""
    if not TABLE_NAME or not ALL_COLUMNS:
        raise HTTPException(status_code=400, detail="No data loaded. Please upload a file first.")
        
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")
        
    try:
        sql_query = text_to_sql(request.prompt, TABLE_NAME, ALL_COLUMNS)
        df_result = pd.read_sql_query(sql_query, sql_conn)
        
        return {
            "sql_command": sql_query,
            "data": df_result.to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))