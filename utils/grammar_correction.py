import streamlit as st
import fitz 
from dotenv import load_dotenv
import os,io
import re
import base64
import tempfile
from io import BytesIO
from google.generativeai import GenerativeModel
import google.generativeai as genai

# Set your Gemini API key
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# Setup Gemini model
model = GenerativeModel("gemini-1.5-flash")  # Use 'gemini-flash' if needed

# --- Streamlit UI ---
st.title("📄 Resume Grammar & Spelling Checker")
uploaded_file = st.file_uploader("Upload your resume (PDF)", type="pdf")


def extract_text_from_pdf(uploaded_file) -> str:
    """
    Save uploaded PDF temporarily and extract full text.

    Returns:
        full_text (str): Extracted text from the PDF.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        temp_path = tmp_file.name

    doc = fitz.open(temp_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    doc.close()

    return full_text


def preprocess_resume_text(text: str) -> str:
    """
    Clean up extracted resume text by removing special symbols and extra whitespace.

    Args:
        text (str): Raw text extracted from PDF.

    Returns:
        str: Cleaned text.
    """
    # Remove special non-ASCII characters
    text = text.encode("ascii", "ignore").decode()

    # Remove unwanted symbols (except basic punctuation)
    text = re.sub(r"[^\w\s.,;:!?@&%()+/\-']", " ", text)

    # Replace multiple spaces/newlines with a single space
    text = re.sub(r"\s+", " ", text)

    # Strip leading/trailing whitespace
    return text.strip()

def get_grammar_suggestions_from_gemini(text: str) -> list:
    """
    Sends the resume text to Gemini and returns a list of (mistake, correction) pairs.
    """
    prompt = f"""You are an expert English editor and proofreader.
    Carefully review the following resume text for any **grammatical mistakes, spelling errors, or incorrect word usage**.
    For each issue you find, respond using this **exact format** on a **new line**:
    ""mistake"" + -> + ""correction""

    Only use this format — do not include explanations or anything else.
    Do not rephrase or improve style. Only correct actual grammar, spelling, or word usage mistakes.

Here is the resume:
{text}
"""

    response = model.generate_content(prompt)
    raw_output = response.text.split("\n")
    return raw_output


if uploaded_file:
    extracted_text = extract_text_from_pdf(uploaded_file)
    preprocessed_text = preprocess_resume_text(extracted_text)
    gemini_response = get_grammar_suggestions_from_gemini(preprocessed_text)
    
    if gemini_response:
        for suggestion in gemini_response:
            if suggestion.strip(): 
                st.markdown(f"🔸 {suggestion}")