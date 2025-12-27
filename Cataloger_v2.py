import streamlit as st
import requests
import pandas as pd
import gender_guesser.detector as gender

# --- CONFIGURATION ---
st.set_page_config(page_title="Research Cataloger Pro", page_icon="🗂️", layout="wide")
st.title("🗂️ Research Cataloger & Metadata Profiler")
st.markdown("""
**Powered by OpenAlex.**
This tool fetches research metadata and automatically profiles:
* **Country of Origin** (based on University)
* **Author Sex** (predicted from First Name)
* **Publication Type**
""")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Search Parameters")
    query = st.text_input("Topic", value="Social Science Philippines")
    
    # Year Range Slider
    year_range = st.slider("Publication Years", 1990, 2025, (2020, 2024))
    
    limit = st.slider("Max Results", 10, 200, 50)
    st.caption("Note: 'Sex' is predicted using the *gender-guesser* library based on first names.")

# --- HELPER: Gender Predictor ---
d = gender.Detector()

def predict_sex(name):
    if not name: return "Unknown"
    # Get first name only
    first_name = name.split()[0]
    guess = d.get_gender(first_name)
    
    # Simplify output
    if "female" in guess: return "Female"
    if "male" in guess: return "Male"
    return "Unknown/Unisex"

# --- MAIN APP ---
if st.button("🚀 Fetch Catalog"):
    
    status = st.empty()
    status.write("🔎 Connecting to OpenAlex API...")
    
    # OpenAlex API URL
    url = "https://api.openalex.org/works"
    
    # Parameters
    params = {
        "search": query,
        "filter": f"from_publication_date:{year_range[0]}-01-01,to_publication_date:{year_range[1]}-12-31",
        "per_page": limit,
        "sort": "relevance_score:desc"
    }
    
    try:
        r = requests.get(url, params=params)
        
        if r.status_code != 200:
            st.error(f"API Error: {r.status_code}")
            st.stop()
            
        data = r.json()
        results = data.get('results', [])
        
        if not results:
            st.warning("No results found. Try broadening your search or year range.")
            st.stop()
            
        status.write(f"✅ Found {len(results)} papers. Profiling Metadata...")
        
        catalog = []
        progress = st.progress(0)
        
        for i, paper in enumerate(results):
            # 1. Title & Year
            title = paper.get('title')
            pub_year = paper.get('publication_year')
            pub_type = paper.get('type', 'article')
            
            # 2. Get Open Access Link (PDF)
            pdf_link = "No Link"
            oa = paper.get('open_access')
            if oa and oa.get('oa_url'):
                pdf_link = oa.get('oa_url')
            
            # 3. Analyze First Author (Country & Sex)
            author_name = "Unknown"
            author_sex = "Unknown"
            country = "Global/Unknown"
            
            authorships = paper.get('authorships', [])
            if authorships:
                # Primary Author
                first_auth = authorships[0]
                author_obj = first_auth.get('author', {})
                author_name = author_obj.get('display_name', 'Unknown')
                
                # Predict Sex
                author_sex = predict_sex(author_name)
                
                # Predict Country from Institution
                insts = first_auth.get('institutions', [])
                if insts:
                    country = insts[0].get('country_code', 'Unknown') 
            
            # 4. Add to List
            catalog.append({
                "Title": title,
                "Year": pub_year,
                "Type": pub_type,
                "Author_Name": author_name,
                "Author_Sex_Pred": author_sex,
                "Country": country, # 2-letter code (e.g., PH, US)
                "Download_Link": pdf_link
            })
            
            progress.progress((i + 1) / len(results))
            
        # --- DISPLAY RESULTS ---
        df = pd.DataFrame(catalog)
        
        # Metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Papers", len(df))
        c2.metric("Open Access", len(df[df['Download_Link'] != 'No Link']))
        c3.metric("Female Authors (Est.)", len(df[df['Author_Sex_Pred'] == 'Female']))
        
        st.dataframe(df, use_container_width=True)
        
        # Download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download Metadata (CSV)",
            csv,
            "research_catalog.csv",
            "text/csv"
        )
        
    except Exception as e:
        st.error(f"Critical Error: {e}")