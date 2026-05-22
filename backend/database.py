import os
import sqlite3
import pandas as pd
import backend.config as config

# Initialize pure in-memory SQLite database
sql_conn = sqlite3.connect(":memory:", check_same_thread=False)

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
    """Builds the SQLite table in RAM from the uploaded dataset."""
    target_file = find_data_file()
    print(f"[*] Processing uploaded file: {target_file}")
    
    df = load_data(target_file)
    
    # Clean column headers for clean, safe SQL syntax execution
    df.columns = [col.strip().replace(' ', '_').replace('-', '_').lower() for col in df.columns]
    
    # Populate In-Memory SQLite Table
    table_name = "dataset"
    df.to_sql(table_name, sql_conn, index=False, if_exists="replace")
    print(f"[✓] Data successfully loaded into in-memory SQLite table: '{table_name}'")

    all_columns = df.columns.tolist()
    
    return table_name, all_columns