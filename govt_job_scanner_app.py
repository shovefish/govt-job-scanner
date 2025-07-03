import streamlit as st
import importlib
import crawler
importlib.reload(crawler)
from crawler import scan_all_sources

st.set_page_config(page_title="Govt Job Scanner", layout="wide")

st.title("🔍 Government Job Scanner for Analytics & Data Science")
st.markdown("Searches all major government departments, PSUs, and research bodies for jobs related to: **Analytics, Data Science, AI, ML, BI, and more.**")

# Keyword input
user_input = st.text_input("Enter keywords (comma-separated)", "analytics, data science")
keywords = [kw.strip().lower() for kw in user_input.split(",") if kw.strip()]

# Trigger scan
if st.button("🔎 Scan Jobs"):
    with st.spinner("Scanning government job portals..."):
        results_df = scan_all_sources(keywords)
    
    if not results_df.empty:
        st.success(f"Found {len(results_df)} job(s) matching your keywords.")
        st.dataframe(results_df[["title", "link", "posted", "experience", "location", "source", "last_date"]])

        csv = results_df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download as CSV", data=csv, file_name="govt_jobs.csv", mime="text/csv")
    else:
        st.warning("No jobs found matching the given keywords.")
