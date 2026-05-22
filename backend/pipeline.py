import json
from groq import Groq
import backend.config as config

# Initialize official Groq client
groq_client = Groq(api_key=config.GROQ_API_KEY)

def text_to_sql(user_prompt: str, table_name: str, all_columns: list) -> str:
    """Uses Groq to translate plain English into valid SQLite commands."""
    
    system_prompt = f"""
    You are a highly accurate Text-to-SQL compiler.
    Convert the user's natural language question into a valid SQLite query string.
    
    Database Context:
    - Target Table Name: {table_name}
    - Available Columns: {', '.join(all_columns)}
    
    Rules:
    - Only query columns that explicitly exist in the database layout.
    - Output your response strictly as a JSON object containing two fields: "reasoning" and "sql_command".
    - Do not wrap the final SQL command inside markdown blocks (such as ```sql).
    - Ensure the SQL command is raw, executable text.
    """

    user_message = f"User Query: {user_prompt}"

    # Query Groq via Llama 3.3 with JSON Mode enabled
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        response_format={"type": "json_object"},
        temperature=0.0
    )
    
    # Parse the structured JSON output
    parsed_json = json.loads(response.choices[0].message.content)
    print(f"\n[Groq LLM Reasoning]: {parsed_json.get('reasoning')}")
    
    return parsed_json.get("sql_command")