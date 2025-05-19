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
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode("utf-8")
    pdf_display = f"""
    <iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800px" type="application/pdf"></iframe>
    """
    st.markdown(pdf_display, unsafe_allow_html=True)

def generate_cover_letter_with_gemini(resume_text: str, job_description: str) -> str:
    prompt = f"""
        You are a career assistant that writes personalized cover letters.

        Given the resume and job description below, do the following:
        1. Extract the candidate's full name (if available).
        2. Identify relevant skills, experience, and projects that align with the job description.
        3. If mentioned, include the candidate’s career goals.
        4. Write a personalized cover letter tailored to the hiring manager.

        Important instructions:
        - Do **NOT** include GitHub or LinkedIn links anywhere in the letter.
        - Use this exact structure:
            - Header with candidate's name, phone number, and email (if available).
            - Date
            - Hiring manager/company address block (use placeholders if necessary).
            - Body (3 short, compelling, and formal paragraphs).
            - Closing with a thank-you and candidate’s name as a signature.

        Resume:
        {resume_text}

        Job Description:
        {job_description}

        Only return the final formatted cover letter — nothing else.
        """
    
    response = model.generate_content(prompt)
    return response.text

def display_cover_letter(cover_letter: str):
    styled_html = f"""
        <div style="
    background-color: #ffffff;
    padding: 30px;
    border-left: 6px solid #0d6efd;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
    white-space: pre-wrap;
    color: #333333;
    line-height: 1.6;
    max-width: 800px;
    margin: 30px auto;
    ">
        {cover_letter.strip()}
        </div>
        """
    st.markdown(styled_html, unsafe_allow_html=True)

if uploaded_file:
    extracted_text = extract_text_from_pdf(uploaded_file)
    preprocessed_text = preprocess_resume_text(extracted_text)
    gemini_response = get_grammar_suggestions_from_gemini(preprocessed_text)
    
    if gemini_response:
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

        st.subheader("You can also create a personalized Cover Letter on the basis of you current resume")
        job_desc = st.text_input("Paste your job description here")

        if job_desc:
            generated_cover_letter = generate_cover_letter_with_gemini(preprocessed_text,job_desc)
            display_cover_letter(generated_cover_letter)