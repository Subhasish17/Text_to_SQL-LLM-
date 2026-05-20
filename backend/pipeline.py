from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import backend.config as config
from backend.database import qdrant_client

# New Google GenAI SDK Client
gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)

# Define the Strict Output Format
class SQLResponse(BaseModel):
    reasoning: str = Field(description="Step-by-step logic on how you matched the text to the columns.")
    sql_command: str = Field(description="The raw, executable SQLite query string. NO markdown formatting.")

def text_to_sql(user_prompt: str, table_name: str, all_columns: list) -> str:
    # 1. Embed user query using the New SDK and New Model
    emb_result = gemini_client.models.embed_content(
        model="gemini-embedding-2",
        contents=user_prompt
    )
    query_vector = emb_result.embeddings[0].values
    
    # 2. Find the top 5 most relevant columns instantly in Qdrant memory
    search_response = qdrant_client.query_points(
        collection_name=config.COLLECTION_NAME,
        query=query_vector,
        limit=5
    )
    
    relevant_columns = [hit.payload["column_name"] for hit in search_response.points]

    # 3. Build the strict prompt
    system_prompt = f"""
    You are a highly accurate Text-to-SQL compiler.
    Convert the user's natural language question into a valid SQLite query.
    
    Database Context:
    - Target Table Name: {table_name}
    - All Available Columns: {', '.join(all_columns)}
    - Most Semantically Relevant Columns: {', '.join(relevant_columns)}
    
    Rules:
    - Only query columns that explicitly exist.
    - Do not use any unsupported SQL functions.
    """

    # 4. Generate Structured JSON Output using the active 2.5 Flash model
    response = gemini_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=system_prompt + "\n\nUser Query: " + user_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SQLResponse,
            temperature=0.0
        )
    )
    
    # Validate and parse the output
    parsed_result = SQLResponse.model_validate_json(response.text)
    print(f"\n[LLM Reasoning]: {parsed_result.reasoning}")
    
    return parsed_result.sql_command