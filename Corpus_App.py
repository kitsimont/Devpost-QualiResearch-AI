import streamlit as st
import requests
import pandas as pd
import io
import fitz  # PyMuPDF
from duckduckgo_search import DDGS
import time

# --- CONFIG ---
st.set_page_config(page_title="Wild Web Corpus Builder", page_icon="🕸️", layout="wide")
st.title("🕸️ Wild Web Corpus Builder (PDF Hunter)")

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔍 Search Criteria")
    topic = st.text_input("Topic", value="Filipino Psychology Social Science")
    target_words = st.number_input("Target Words", value=20000, step=5000)
    max_results = st.slider("Max Links to Check", 50, 500, 100)
    st.info("Strategy: This searches the open web for direct PDF files (filetype:pdf), bypassing academic firewalls.")

# --- FUNCTIONS ---
def get_pdf_text(url):
    """Downloads and reads a PDF from a direct URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200 and 'application/pdf' in response.headers.get('Content-Type', '').lower():
            with fitz.open(stream=response.content, filetype="pdf") as doc:
                text = ""
                for page in doc:
                    text += page.get_text()
            return text
        return None
    except:
        return None

# --- MAIN APP ---
if st.button("🚀 Start Hunter"):
    
    # UI Setup
    pbar = st.progress(0)
    log = st.empty()
    metric = st.empty()
    
    # Search Query: Force PDF filetype
    query = f'{topic} filetype:pdf'
    log.info(f"🔎 Searching DuckDuckGo for: `{query}`...")
    
    # 1. Get Links
    pdf_links = []
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))
        for r in results:
            pdf_links.append({"title": r['title'], "url": r['href']})
            
    log.success(f"✅ Found {len(pdf_links)} PDF links. Starting download...")
    
    # 2. Download & Extract
    corpus = []
    total_words = 0
    
    for i, link in enumerate(pdf_links):
        if total_words >= target_words:
            break
            
        title = link['title']
        url = link['url']
        
        log.write(f"⬇️ ({i+1}/{len(pdf_links)}) Downloading: **{title[:40]}...**")
        
        text = get_pdf_text(url)
        
        if text and len(text) > 1000:
            words = len(text.split())
            total_words += words
            
            corpus.append({
                "Title": title,
                "Word_Count": words,
                "URL": url,
                "Text_Body": text
            })
            
            # Update UI
            metric.metric("Total Words", f"{total_words:,}", f"+{words}")
            pbar.progress(min(total_words / target_words, 1.0))
        
        else:
            print(f"Skipped {url}")
            
    # 3. Finish
    if corpus:
        st.balloons()
        df = pd.DataFrame(corpus)
        st.success(f"🎉 Mission Complete! Collected {total_words:,} words from {len(df)} documents.")
        
        # Download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Wild Corpus (CSV)", csv, "wild_corpus.csv", "text/csv")
        
        # Preview
        st.dataframe(df[['Title', 'Word_Count', 'URL']].head())
    else:
        st.error("❌ Could not download enough text. Try a different topic.")