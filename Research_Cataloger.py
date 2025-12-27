import streamlit as st
import requests
import pandas as pd
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Research Cataloger", page_icon="🗂️", layout="wide")
st.title("🗂️ Research Metadata Scraper")
st.markdown("""
This tool builds a **Bibliography Dataset**. It fetches metadata (Authors, Links, Affiliations) 
instead of downloading full text, allowing for rapid scanning of hundreds of papers.
""")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Search Parameters")
    query = st.text_input("Topic", value="Social Science Philippines")
    year_start = st.number_input("Start Year", 2000, 2025, 2018)
    limit = st.slider("Number of Papers", 10, 500, 100)
    st.info("Note: 'Country' is inferred from the author's university affiliation.")

# --- HELPER: Country Guesser ---
def infer_country(affiliation_name):
    """Simple heuristic to guess country from university name."""
    if not affiliation_name:
        return "Unknown"
    
    aff = affiliation_name.lower()
    if "philippines" in aff or "manila" in aff or "diliman" in aff or "lasalle" in aff or "ateneo" in aff:
        return "Philippines"
    if "usa" in aff or "united states" in aff or "california" in aff or "harvard" in aff:
        return "USA"
    if "uk" in aff or "london" in aff or "oxford" in aff:
        return "UK"
    if "singapore" in aff or "nus" in aff:
        return "Singapore"
    if "australia" in aff:
        return "Australia"
    return "International"

# --- MAIN APP ---
if st.button("🚀 Build Catalog"):
    
    status = st.empty()
    status.write("🔎 Connecting to Semantic Scholar Graph API...")
    
    # API Endpoint
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    
    # We request specific metadata fields
    fields = "title,year,authors.name,authors.affiliations,openAccessPdf,url,publicationTypes,venue"
    
    params = {
        "query": query,
        "year": f"{year_start}-2025",
        "limit": limit,
        "fields": fields
    }
    
    try:
        r = requests.get(url, params=params).json()
        
        if "data" not in r:
            st.error("❌ No results found. Try a different topic.")
            st.stop()
            
        papers = r['data']
        catalog = []
        
        status.write(f"✅ API Success. Processing {len(papers)} papers...")
        progress = st.progress(0)
        
        for i, p in enumerate(papers):
            # 1. Get Primary Author Info
            first_author = "Unknown"
            country_origin = "Unknown"
            
            if p.get('authors') and len(p['authors']) > 0:
                auth_data = p['authors'][0] # Take the first author
                first_author = auth_data.get('name')
                
                # Try to find affiliation
                if auth_data.get('affiliations'):
                    aff_list = auth_data.get('affiliations')
                    if aff_list:
                        # Use the first affiliation to guess country
                        school = aff_list[0]
                        country_origin = infer_country(school)
            
            # 2. Get Link (Prioritize PDF, then General URL)
            pdf_link = "Not Available"
            if p.get('openAccessPdf'):
                pdf_link = p['openAccessPdf'].get('url')
            elif p.get('url'):
                pdf_link = p.get('url')
            
            # 3. Clean Publication Type
            pub_type = "Article"
            if p.get('publicationTypes'):
                pub_type = ", ".join(p['publicationTypes'])
            
            # 4. Add to List
            catalog.append({
                "Title": p.get('title'),
                "Year": p.get('year'),
                "First_Author": first_author,
                "Inferred_Country": country_origin,
                "Type": pub_type,
                "Link": pdf_link,
                "Sex_Prediction": "Needs Manual Review" # Placeholder column
            })
            
            progress.progress((i + 1) / len(papers))
            
        # --- OUTPUT ---
        df = pd.DataFrame(catalog)
        
        st.success(f"🎉 Catalog Complete! Found {len(df)} papers.")
        
        # Display
        st.dataframe(df, use_container_width=True)
        
        # Download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download Catalog (CSV)",
            csv,
            "research_catalog.csv",
            "text/csv"
        )
        
    except Exception as e:
        st.error(f"Error: {e}")