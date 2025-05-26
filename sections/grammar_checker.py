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
from PIL import Image

# Set your Gemini API key
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# Setup Gemini model
model = GenerativeModel("gemini-1.5-flash")  # Use 'gemini-flash' if needed

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
    prompt =  f"""You are an expert English editor and proofreader.
    Carefully review the following resume text for any **clear grammatical mistakes, definite spelling errors, or obviously incorrect word usage**.

    Do **not** make style or rephrasing suggestions.
    Do **not** suggest changes unless the mistake is clearly wrong.
    Do **not** be overly cautious — only point out **actual, unambiguous errors**.

    For each real issue you find, respond using this **exact format** on a **new line**, and keep both the mistake and correction inside **double quotation marks**:
    "mistake" + -> + "correction"

    Only use this format — do not include explanations or anything else.

    Here is the resume:
    {text}
    """
    response = model.generate_content(prompt)
    raw_output = response.text.strip()
    return raw_output

def extract_mistakes_from_gemini(text):
    """
    Extracts all phrases before '→' symbol in the gemini output.
    """
    raw_lines = text.strip().split("\n")
    mistakes = []
    for line in raw_lines:
        if '->' in line:
            parts = line.strip().split("->")
            if len(parts) == 2:
                mistake = parts[0].strip().strip('"')
                mistakes.append(mistake)
    return mistakes

def highlight_mistakes_in_pdf(uploaded_file, mistakes):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        temp_path = tmp_file.name

    doc = fitz.open(temp_path)

    for page in doc:
        for mistake in mistakes:
            text_instances = page.search_for(mistake)
            for inst in text_instances:
                highlight = page.add_highlight_annot(inst)
                highlight.set_info(title="Grammar Issue", content=f"{mistake}")
                highlight.update()

    highlighted_pdf_path = os.path.join(tempfile.gettempdir(), "highlighted_resume.pdf")
    doc.save(highlighted_pdf_path, garbage=4, deflate=True, clean=True)
    doc.close()
    return highlighted_pdf_path

def display_pdf(file_path):
    doc = fitz.open(file_path)
    for page in doc:
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        st.image(img)

def run():
 
    st.title("📄 Grammer and Spelling Check")
    uploaded_file = st.file_uploader("Upload your resume (PDF)", type="pdf")

    if uploaded_file:
        extracted_text = extract_text_from_pdf(uploaded_file)
        preprocessed_text = preprocess_resume_text(extracted_text)
        gemini_response = get_grammar_suggestions_from_gemini(preprocessed_text)

        check_grammer = st.button("View Errors")
        if check_grammer and gemini_response:
            # st.text(gemini_response)
            mistakes = extract_mistakes_from_gemini(gemini_response)
            st.subheader("Grammer and spelling errors")

            for line in gemini_response.strip().split("\n"):
                if "->" in line:
                    st.markdown(f"🔸 `{line.strip()}`")
                    
            st.subheader("Highlighted PDF with mistakes")
            uploaded_file.seek(0)
            highlighted_pdf_path = highlight_mistakes_in_pdf(uploaded_file,mistakes)
            display_pdf(highlighted_pdf_path)