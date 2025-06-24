# main.py
import streamlit as st
import pandas as pd
from crawler import scan_all_sources

st.set_page_config(page_title="Govt Job Scanner", layout="wide")
st.title("🔎 Government Jobs for Data/Analytics - Scanner")

st.markdown("""
Searches all major government departments, PSUs, and research bodies for jobs related to:
**Analytics**, **Data Science**, **AI**, **ML**, **BI**, and more.
""")

keywords_input = st.text_input("Enter keywords (comma separated)", "data,analytics,AI,ML,BI")
keywords = [kw.strip().lower() for kw in keywords_input.split(",") if kw.strip()]

if st.button("🔍 Scan Now"):
    with st.spinner("Scanning across 20+ portals..."):
        results = scan_all_sources(keywords)
        if results.empty:
            st.warning("No jobs found with the given keywords.")
        else:
            st.success(f"Found {len(results)} matching jobs!")
            st.dataframe(results)
            csv = results.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV", csv, "govt_jobs.csv", "text/csv")
