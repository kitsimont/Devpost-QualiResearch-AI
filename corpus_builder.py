import requests
import pandas as pd
import io
import PyPDF2
from tqdm import tqdm
import time

# --- CONFIGURATION ---
TARGET_WORDS = 1000000  # 1 Million Words
SEARCH_QUERY = "Social Science Philippines"
START_YEAR = 2020
BATCH_SIZE = 100  # How many papers to ask API for at once

def get_text_from_pdf_url(url):
    """Downloads a PDF from a URL and extracts text."""
    try:
        # Fake a browser header so servers don't block us
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            f = io.BytesIO(response.content)
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        return None
    except:
        return None

def build_million_word_corpus():
    total_words_collected = 0
    corpus_data = []
    offset = 0
    
    # Progress bar setup
    pbar = tqdm(total=TARGET_WORDS, desc="Harvesting Words", unit="word")
    
    print(f"🚀 Starting Harvest for '{SEARCH_QUERY}'...")
    print("This will prioritize OPEN ACCESS papers with PDF links.")

    while total_words_collected < TARGET_WORDS:
        # 1. Search API
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": SEARCH_QUERY,
            "year": f"{START_YEAR}-2025",
            "limit": BATCH_SIZE,
            "offset": offset,
            "openAccessPdf": "", # Filter: Must have PDF
            "fields": "title,year,openAccessPdf"
        }
        
        try:
            r = requests.get(url, params=params).json()
            if "data" not in r:
                print("❌ No more papers found.")
                break
                
            papers = r['data']
            
            # 2. Process Batch
            for paper in papers:
                pdf_info = paper.get('openAccessPdf')
                
                if pdf_info and pdf_info.get('url'):
                    pdf_url = pdf_info.get('url')
                    
                    # Try to get Full Text
                    full_text = get_text_from_pdf_url(pdf_url)
                    
                    if full_text and len(full_text) > 1000:
                        word_count = len(full_text.split())
                        
                        # Add to Dataset
                        corpus_data.append({
                            "year": paper.get('year'),
                            "title": paper.get('title'),
                            "word_count": word_count,
                            "text": full_text, # The gold!
                            "source_url": pdf_url
                        })
                        
                        # Update Counts
                        total_words_collected += word_count
                        pbar.update(word_count)
                        
                        if total_words_collected >= TARGET_WORDS:
                            break
            
            # Move to next page of results
            offset += BATCH_SIZE
            time.sleep(1) # Be nice to the API
            
        except Exception as e:
            print(f"Error: {e}")
            break

    pbar.close()
    
    # 3. Save to CSV
    if corpus_data:
        df = pd.DataFrame(corpus_data)
        filename = "million_word_corpus.csv"
        df.to_csv(filename, index=False)
        print(f"\n✅ DONE! Collected {total_words_collected} words from {len(df)} papers.")
        print(f"💾 Saved to {filename}")
    else:
        print("❌ Failed to collect data.")

if __name__ == "__main__":
    build_million_word_corpus()