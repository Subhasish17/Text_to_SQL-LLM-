import streamlit as st
import requests
import pandas as pd

# Page Configuration
st.set_page_config(page_title="AI Data Explorer", layout="wide", initial_sidebar_state="expanded")
st.title("⚡ Groq-Powered Data Dashboard")
st.caption("Upload a file, then ask questions in plain English to instantly generate and execute SQL.")

# API Endpoints
BACKEND_URL = "http://127.0.0.1:8000"
UPLOAD_ENDPOINT = f"{BACKEND_URL}/api/upload"
QUERY_ENDPOINT = f"{BACKEND_URL}/api/query"

# Initialize session state to track if data is loaded
if 'data_ready' not in st.session_state:
    st.session_state['data_ready'] = False

# ==========================================
# SIDEBAR: DATA UPLOAD & PROCESSING
# ==========================================
with st.sidebar:
    st.header("📂 Data Source")
    st.write("Upload a dataset to initialize the memory database.")
    
    uploaded_file = st.file_uploader("Upload CSV or JSON", type=['csv', 'json'])
    
    if uploaded_file is not None:
        if st.button("Process & Load File", type="primary", use_container_width=True):
            with st.spinner("Loading data into pure-RAM SQLite database..."):
                try:
                    # Prepare the file to be sent via POST request
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    upload_response = requests.post(UPLOAD_ENDPOINT, files=files)
                    
                    if upload_response.status_code == 200:
                        payload = upload_response.json()
                        st.success(f"✅ {uploaded_file.name} is ready!")
                        st.session_state['data_ready'] = True
                        st.session_state['columns'] = payload.get("columns", [])
                    else:
                        st.error(f"Upload failed: {upload_response.json().get('detail')}")
                        st.session_state['data_ready'] = False
                except requests.exceptions.ConnectionError:
                    st.error("❌ Could not connect to backend. Is FastAPI running?")

    if st.session_state.get('data_ready'):
        st.divider()
        st.subheader("Available Columns:")
        for col in st.session_state.get('columns', []):
            st.markdown(f"- `{col}`")

# ==========================================
# MAIN DASHBOARD: QUERY INTERFACE
# ==========================================
if st.session_state.get('data_ready'):
    st.divider()
    
    # Query Input
    user_input = st.text_input(
        "What would you like to know about your data?",
        placeholder="e.g., Show me the top 5 rows sorted by salary descending..."
    )

    if st.button("Generate & Run Query"):
        if user_input.strip():
            # Updated spinner text for Groq
            with st.spinner("Compiling SQL at lightning speed via Groq..."):
                try:
                    api_response = requests.post(QUERY_ENDPOINT, json={"prompt": user_input})
                    
                    if api_response.status_code == 200:
                        result_payload = api_response.json()
                        
                        # Layout for Results
                        col1, col2 = st.columns([1, 2.5])
                        
                        # Left Column: Show the Generated SQL
                        with col1:
                            st.info("⚙️ **Generated SQL Command:**")
                            st.code(result_payload["sql_command"], language="sql")
                            
                        # Right Column: Show the Data Table
                        with col2:
                            st.success("📊 **Retrieved Results:**")
                            records = result_payload["data"]
                            
                            if records:
                                # Convert the JSON records back to a DataFrame for clean rendering
                                output_df = pd.DataFrame(records)
                                st.dataframe(output_df, use_container_width=True, hide_index=True)
                            else:
                                st.warning("Query executed successfully, but returned zero matched rows.")
                                
                    else:
                        st.error(f"Execution Error: {api_response.json().get('detail')}")
                        
                except requests.exceptions.ConnectionError:
                    st.error("❌ Could not connect to the Backend API. Make sure uvicorn is running.")
        else:
            st.warning("Please type a question into the text field.")
else:
    # Updated placeholder state for the new architecture
    st.info("👈 Please upload and process a CSV or JSON file from the sidebar to begin.")
    st.markdown("---")
    st.markdown("""
    ### How it works:
    1. **Upload** your dataset via the sidebar.
    2. The backend **instantly loads** your data into a pure-RAM SQLite database.
    3. Type your question in **plain English**.
    4. **Groq (Llama 3)** reads your schema and generates **deterministic SQL** at lightning speed.
    5. The SQL executes directly against your data for zero-latency rendering.
    """)