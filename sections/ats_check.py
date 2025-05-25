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

def get_ats_feedback_from_gemini(resume_text: str, job_description: str) -> dict:
    """
    Sends resume and job description to Gemini and returns:
    - ATS score (out of 100)
    - Strong points in the resume
    - Weaknesses/improvements in the resume
    """
    prompt = f"""
    You are an skilled ATS (Applicant Tracking System) scanner with a deep understanding of Data science or Full Stack Web Development or Big Data or Cloud Engineering or Android Development or IOS Development or Any field that is relevent to user's resume and ATS functionality, 
    your task is to evaluate the resume against the provided job description.

    Please follow this **strict format** exactly so it is easy to parse:

    ATS Score: <score out of 100>

    Strong Points:
    - <strong point 1>
    - <strong point 2>
    ...

    Weaknesses / Areas to Improve:
    - <weakness 1>
    - <weakness 2>
    ...

    Only use the above format. Do not include explanations or any additional text outside of these sections.

    Resume:
    {resume_text}

    Job Description:
    {job_description}
    """

    response = model.generate_content(prompt)
    raw_output = response.text.strip()

    # You may optionally parse the output into a dictionary
    return raw_output

def parse_ats_feedback(text: str) -> dict:
    """
    Parses the plain text ATS feedback from Gemini into a structured dictionary.
    Expected format:
    ATS Score: <score>

    Strong Points:
    - point1
    - point2
    ...

    Weaknesses / Areas to Improve:
    - point1
    - point2
    ...
    """
    lines = text.strip().splitlines()
    score = None
    strengths = []
    weaknesses = []
    section = None

    for line in lines:
        line = line.strip()
        if line.startswith("ATS Score:"):
            try:
                score = int(line.split(":")[1].strip())
            except ValueError:
                score = None
        elif line.startswith("Strong Points"):
            section = "strengths"
        elif line.startswith("Weaknesses") or line.startswith("Areas to Improve"):
            section = "weaknesses"
        elif line.startswith("- "):
            if section == "strengths":
                strengths.append(line[2:].strip())
            elif section == "weaknesses":
                weaknesses.append(line[2:].strip())

    return {
        "score": score,
        "strengths": strengths,
        "weaknesses": weaknesses
    }

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

def run():

    # --- Streamlit UI ---
    st.title("📄 ATS Scorer & Analyzer")
    job_text = st.text_input("Paste your job description here")
    uploaded_file = st.file_uploader("Upload your resume (PDF)", type="pdf")

    if uploaded_file:
        st.success("Pdf uploaded sucessfully")

    checkATS_button = st.button("Check ATS score")

    if checkATS_button: 

        if uploaded_file and job_text:
            extracted_text = extract_text_from_pdf(uploaded_file)
            preprocessed_text = preprocess_resume_text(extracted_text)
            gemini_response = get_ats_feedback_from_gemini(preprocessed_text,job_text)
            parsed_response = parse_ats_feedback(gemini_response)
            
        
            st.subheader("✅ ATS Score")
            st.markdown(f"**Score:** {parsed_response['score']} / 100")

            st.subheader("💪 Strong Points")
            for point in parsed_response["strengths"]:
                st.markdown(f"- {point}")

            st.subheader("⚠️ Weaknesses / Areas to Improve")
            for point in parsed_response["weaknesses"]:
                st.markdown(f"- {point}")

            st.subheader("Here is your personalized Cover Letter on the basis of you current resume and job description")

            generated_cover_letter = generate_cover_letter_with_gemini(preprocessed_text,job_text)
            display_cover_letter(generated_cover_letter)

        else:
            st.warning("Please upload your resume and Job description")