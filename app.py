import streamlit as st
import pandas as pd
import json
from google import genai
from google.genai import types

# Set up page config
st.set_page_config(page_title="Target vs Achieved Extractor", layout="wide")

st.title("📊 Target vs Achieved Data Extraction Tool")
st.write("Extract data from your text messages and update the tracking sheet for Mar 2026.")

# Sidebar for API Key
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Enter your Gemini API Key", type="password")

# Initialize the model (using Gemini 3 Flash or equivalent stable model)
if api_key:
    client = genai.Client(api_key=api_key)
else:
    st.sidebar.warning("Please enter your Gemini API Key to continue.")

# Define the structure of the data based on your spreadsheet
@st.cache_data
def load_base_dataframe():
    data = {
        "Metric": [
            "Total Spends", "Total Leadgen Spends", "Total Branding Spends",
            "Leads", "CPL", "Qualified", "CPQL",
            "Presales SVS", "Presales SVC",
            "Walkin Direct SVC", "CP SVC", "CP/PS Clash",
            "Total Physical SVC", "Revisits",
            "Digital Bookings", "Direct Bookings", "CP Bookings", "Total Bookings"
        ],
        "Week 1 Target": [235000, 225000, 10000, 150, 1500, 40, 5625, 20, 10, 5, 15, 0, 100, 30, 1, 1, 1, 3],
        "Week 1 Achieved": ["" for _ in range(18)],
        "Week 2 Target": [235000, 225000, 10000, 150, 1500, 40, 5625, 20, 10, 5, 15, 0, 100, 30, 1, 1, 1, 3],
        "Week 2 Achieved": ["" for _ in range(18)],
        "Week 3 Target": [240000, 225000, 15000, 150, 1500, 40, 5625, 20, 10, 5, 15, 0, 100, 30, 1, 1, 1, 3],
        "Week 3 Achieved": ["" for _ in range(18)],
        "Week 4 Target": ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""], # Set targets for week 4 as needed
        "Week 4 Achieved": ["" for _ in range(18)],
    }
    return pd.DataFrame(data)

df = load_base_dataframe()

# Initialize session state to hold dataframe across interactions
if "df_state" not in st.session_state:
    st.session_state["df_state"] = df.copy()

# User Input
col1, col2 = st.columns([2, 1])

with col1:
    user_message = st.text_area(
        "Paste your text message/update here:",
        height=250,
        placeholder="Example: Total spend is 200,000 this week. Leads generated: 140. Total Bookings: 2..."
    )

with col2:
    selected_week = st.selectbox("Select the week to update:", ["Week 1", "Week 2", "Week 3", "Week 4"])
    process_button = st.button("Extract and Update", type="primary")

if process_button and api_key and user_message:
    try:
        # Prompt definition for LLM extraction
        prompt = f"""
        You are an intelligent data extraction assistant. Given the following message for {selected_week}, extract the achieved values for the metrics listed below. Return a valid JSON object only. If a metric is not mentioned in the text, leave the value empty or null.

        Metrics to extract:
        - Total Spends
        - Total Leadgen Spends
        - Total Branding Spends
        - Leads
        - CPL
        - Qualified
        - CPQL
        - Presales SVS
        - Presales SVC
        - Walkin Direct SVC
        - CP SVC
        - CP/PS Clash
        - Total Physical SVC
        - Revisits
        - Digital Bookings
        - Direct Bookings
        - CP Bookings
        - Total Bookings

        User Message:
        "{user_message}"
        """
        
        # Call Gemini 3 Flash or appropriate generative model
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        extracted_data = json.loads(response.text)
        st.success("Extraction successful!")
        
        # Update the session state DataFrame for the selected week
        week_col = f"{selected_week} Achieved"
        
        # Map values from JSON keys to metric rows
        metric_mapping = {
            "Total Spends": 0,
            "Total Leadgen Spends": 1,
            "Total Branding Spends": 2,
            "Leads": 3,
            "CPL": 4,
            "Qualified": 5,
            "CPQL": 6,
            "Presales SVS": 7,
            "Presales SVC": 8,
            "Walkin Direct SVC": 9,
            "CP SVC": 10,
            "CP/PS Clash": 11,
            "Total Physical SVC": 12,
            "Revisits": 13,
            "Digital Bookings": 14,
            "Direct Bookings": 15,
            "CP Bookings": 16,
            "Total Bookings": 17,
        }
        
        for key, row_idx in metric_mapping.items():
            if key in extracted_data and extracted_data[key] is not None:
                st.session_state["df_state"].at[row_idx, week_col] = extracted_data[key]
                
    except Exception as e:
        st.error(f"Failed to process message. Error: {e}")

# Display the Data
st.markdown("---")
st.subheader("Current Tracking Sheet Data")

# Use editable dataframe so the user can manually correct or review values
edited_df = st.data_editor(st.session_state["df_state"], use_container_width=True)
st.session_state["df_state"] = edited_df

# Download as CSV option
csv = st.session_state["df_state"].to_csv(index=False).encode('utf-8')
st.download_button(
    "📥 Download updated data as CSV",
    data=csv,
    file_name=f"target_achieved_mar2026.csv",
    mime="text/csv"
)
