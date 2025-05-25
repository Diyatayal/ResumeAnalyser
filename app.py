import streamlit as st
from sections import grammar_checker, homepage,ats_check,jobs,admin_panel

st.set_page_config(page_title="Resume Analyzer", layout="wide",page_icon="🤖")

st.sidebar.title("Select Feature")
app_mode = st.sidebar.selectbox("Go to", ["Homepage", "ATS Score Check", "Grammar Checker", "Find Jobs","Admin Panel"])

# Page router
if app_mode == "Homepage":
    homepage.run()

elif app_mode == "ATS Score Check":
    ats_check.run()

elif app_mode == "Grammar Checker":
    grammar_checker.run()

elif app_mode == "Find Jobs":
    jobs.run()

elif app_mode == "Admin Panel":
    admin_panel.run()