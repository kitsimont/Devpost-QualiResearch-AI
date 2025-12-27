import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import PyPDF2
import pandas as pd
import io

# --- 1. SETUP & AUTH ---
load_dotenv("sec.env")
api_key = os.getenv("GOOGLE_API_KEY")

st.set_page_config(page_title="QualiResearch AI", page_icon="🧬", layout="wide")

# Valid Key Check
if not api_key:
    st.error("❌ Missing API Key in sec.env")
    st.stop()

# Clean key just in case (removes spaces/brackets)
api_key = api_key.strip().replace("[", "").replace("]", "")
genai.configure(api_key=api_key)

# --- 2. SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Research Controls")
    
    # We strictly use the Flash model for now because it is the most stable
   # --- 2. SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Research Controls")
    
    # AUTOMATIC MODEL LOADER
    try:
        with open("latest-model.txt", "r") as f:
            auto_model = f.read().strip()
    except:
        auto_model = "gemini-2.5-flash" # Fallback
        
    st.success(f"🤖 Connected to: {auto_model}")
    model_choice = auto_model
    
    st.divider()
    
    st.subheader("📘 The Codebook")
    default_codebook = """
    Themes: Leadership, Resilience, Community Trust, Challenges
    Sentiment: Positive, Negative, Neutral
    """
    codebook = st.text_area("Define Tags", value=default_codebook, height=150)

# --- 3. HELPER FUNCTIONS ---
def extract_text(uploaded_file):
    try:
        reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        return None

def analyze_data(text, codebook, model_name):
    # DEBUG: Print what we are sending
    print(f"Calling model: {model_name}...")
    
    # CRITICAL FIX: Ensure parentheses () are used, NOT brackets []
    model = genai.GenerativeModel(model_name) 
    
    prompt = f"""
    Act as a Data Analyst.
    Analyze the text below using these themes: {codebook}
    
    Output a CSV with headers: Quote|Theme|Sentiment|Reasoning
    
    TEXT:
    {text[:10000]}
    """
    
    response = model.generate_content(prompt)
    return response.text

# --- 4. MAIN INTERFACE ---
st.title("🧬 QualiResearch: Auto-Tagger")

uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

if uploaded_file:
    text = extract_text(uploaded_file)
    if text:
        st.success("PDF Read Successfully")
        
        if st.button("🚀 Run Analysis"):
            with st.spinner("Analyzing..."):
                try:
                    # Run the analysis
                    result = analyze_data(text, codebook, model_choice)
                    
                    # Clean the Markdown
                    clean_csv = result.replace("```csv", "").replace("```", "").strip()
                    
                    # Show Data
                    df = pd.read_csv(io.StringIO(clean_csv), sep="|")
                    st.dataframe(df)
                    
                except Exception as e:
                    st.error(f"Error: {e}")