import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from docx import Document
import re
import io
import zipfile

# --- CONFIGURATION ---
st.set_page_config(page_title="Corpus Scrubber", page_icon="🧽", layout="wide")

st.title("🧽 Corpus Scrubber: Bulk Document Cleaner")
st.markdown("""
**Upload multiple PDF or DOCX files.** This tool will extract text, remove noise (citations, numbers, punctuation), 
and prepare it for corpus linguistics or machine learning.
""")

# --- 1. CLEANING FUNCTIONS ---
def get_text_from_pdf(file_bytes):
    """Fast extraction using PyMuPDF"""
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        return ""

def get_text_from_docx(file_bytes):
    """Extraction using python-docx"""
    try:
        doc = Document(io.BytesIO(file_bytes))
        full_text = [para.text for para in doc.paragraphs]
        return '\n'.join(full_text)
    except Exception as e:
        return ""

def clean_text_logic(text, config):
    """The Master Cleaning Function"""
    if not text: return ""

    # A. Structural Cleaning (The "Big Cuts")
    # 1. References Section
    if config['remove_refs']:
        # Cuts text after "References" if it appears on a new line
        text = re.sub(r'(?i)(\n|\r)\s*(references|bibliography|works cited)\s*(\n|\r).*', '', text, flags=re.DOTALL)
    
    # 2. URLs & Emails
    if config['remove_urls']:
        text = re.sub(r'http\S+|www\.\S+', '', text)
        text = re.sub(r'\S+@\S+', '', text)

    # 3. PDF Artifacts (Hyphenation)
    if config['fix_hyphens']:
        # "respon- sibility" -> "responsibility"
        text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)

    # B. Noise Removal (The "Scrubbing")
    # 4. Citations (Academic specific)
    if config['remove_citations']:
        # Remove (Smith, 2020) or (Smith et al., 2020)
        text = re.sub(r'\([A-Za-z\s\.,]+,?\s?\d{4}\)', '', text)
        # Remove [1], [12], [1-5]
        text = re.sub(r'\[\d+([–-]\d+)?\]', '', text)

    # 5. Numbers
    if config['remove_numbers']:
        text = re.sub(r'\d+', '', text)

    # 6. Punctuation
    if config['remove_punct']:
        # Replace punctuation with space to prevent word merging
        text = re.sub(r'[^\w\s]', ' ', text)

    # 7. Lowercase
    if config['lowercase']:
        text = text.lower()

    # C. Final Polish
    # Collapse multiple spaces into one
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

# --- 2. SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("⚙️ Scrubbing Settings")
    
    st.subheader("Structure")
    cfg_refs = st.checkbox("Cut 'References' Section", value=True)
    cfg_hyphens = st.checkbox("Fix Line-Break Hyphens", value=True)
    cfg_urls = st.checkbox("Remove URLs & Emails", value=True)
    
    st.subheader("Content")
    cfg_cite = st.checkbox("Remove Citations (Smith, 2020)", value=True)
    cfg_num = st.checkbox("Remove Numbers", value=True)
    cfg_punct = st.checkbox("Remove Punctuation", value=True)
    cfg_lower = st.checkbox("Convert to Lowercase", value=False)
    
    # Pack config into dictionary
    clean_config = {
        'remove_refs': cfg_refs,
        'fix_hyphens': cfg_hyphens,
        'remove_urls': cfg_urls,
        'remove_citations': cfg_cite,
        'remove_numbers': cfg_num,
        'remove_punct': cfg_punct,
        'lowercase': cfg_lower
    }
    
    st.divider()
    output_format = st.radio("Output Format", ["CSV (Spreadsheet)", "TXT Files (ZIP)"])

# --- 3. MAIN APP ---
uploaded_files = st.file_uploader("Upload Files (PDF or DOCX)", type=['pdf', 'docx'], accept_multiple_files=True)

if uploaded_files:
    if st.button("🚀 Scrub & Process"):
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        cleaned_corpus = []
        total_files = len(uploaded_files)
        
        # --- PROCESSING LOOP ---
        for i, file in enumerate(uploaded_files):
            file_name = file.name
            status_text.write(f"Processing: **{file_name}**...")
            
            # 1. Read File
            file_bytes = file.read()
            raw_text = ""
            
            if file_name.endswith('.pdf'):
                raw_text = get_text_from_pdf(file_bytes)
            elif file_name.endswith('.docx'):
                raw_text = get_text_from_docx(file_bytes)
                
            # 2. Clean Text
            clean_text = clean_text_logic(raw_text, clean_config)
            
            # 3. Store Result
            cleaned_corpus.append({
                "filename": file_name,
                "original_len": len(raw_text),
                "cleaned_len": len(clean_text),
                "text": clean_text
            })
            
            progress_bar.progress((i + 1) / total_files)
            
        status_text.success(f"✅ Finished processing {total_files} files!")
        
        # --- DOWNLOAD LOGIC ---
        if output_format == "CSV (Spreadsheet)":
            # OPTION A: CSV
            df = pd.DataFrame(cleaned_corpus)
            st.dataframe(df.head())
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download Cleaned CSV",
                csv,
                "scrubbed_corpus.csv",
                "text/csv"
            )
            
        else:
            # OPTION B: ZIP of TXT Files
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                for item in cleaned_corpus:
                    # Create a clean filename (e.g., "doc1.pdf" -> "doc1.txt")
                    txt_name = item['filename'].rsplit('.', 1)[0] + ".txt"
                    zf.writestr(txt_name, item['text'])
            
            st.download_button(
                "📥 Download ZIP of Text Files",
                zip_buffer.getvalue(),
                "scrubbed_corpus.zip",
                "application/zip"
            )