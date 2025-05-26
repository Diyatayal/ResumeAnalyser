# resume_builder.py
from dotenv import load_dotenv
import os
import streamlit as st
from fpdf import FPDF
from google.generativeai import GenerativeModel
import google.generativeai as genai

# === Configure Gemini API ===
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = GenerativeModel("gemini-1.5-flash")

# === Generate Summary with Gemini ===
def generate_summary(skills, experience):
    prompt = f"Write a 2-3 line professional summary for a data scientist with skills: {skills} and experience: {experience}."
    response = model.generate_content(prompt)
    return response.text.strip()

# === Resume PDF Generator ===
class PDF(FPDF):
    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_name = name  # store name

    def header(self):
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, self.user_name, ln=True, align="C")  # use name instead of "Resume"

    def section_title(self, title):
        self.set_font("Arial", "B", 12)
        self.set_text_color(30, 30, 30)
        self.cell(0, 10, title, ln=True)

    def section_body(self, body):
        self.set_font("Arial", "", 11)
        self.multi_cell(0, 8, body)
        self.ln(1)

def export_to_pdf(data, template):
    pdf = PDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, data["name"], ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f'{data["email"]} | {data["phone"]} | {data["linkedin"]}', ln=True)

    pdf.section_title("Professional Summary")
    pdf.section_body(data["summary"])

    pdf.section_title("Education")
    for edu in data["education"]:
        pdf.section_body(f"{edu['degree']} at {edu['school']} ({edu['year']})")

    pdf.section_title("Experience")
    for exp in data["experience"]:
        pdf.section_body(f"{exp['role']} at {exp['company']} ({exp['duration']})\n- {exp['desc']}")

    pdf.section_title("Projects")
    for proj in data["projects"]:
        pdf.section_body(f"{proj['title']} - {proj['desc']}")

    pdf.section_title("Skills")
    pdf.section_body(", ".join(data["skills"]))

    pdf.section_title("Soft Skills")
    pdf.section_body(", ".join(data["soft_skills"]))

    pdf.section_title("Languages")
    pdf.section_body(", ".join(data["languages"]))

    pdf.section_title("Tools & Technologies")
    pdf.section_body(", ".join(data["tools"]))

    pdf_bytes = bytes(pdf.output(dest="S"))
    return pdf_bytes
# === Streamlit App UI ===
st.title("📝 AI Resume Builder")
template = st.selectbox("Choose a Resume Template", ["Modern", "Professional", "Creative"])

st.header("🔗 Personal Info")
name = st.text_input("Full Name")
email = st.text_input("Email")
phone = st.text_input("Phone Number")
linkedin = st.text_input("LinkedIn URL")

st.header("💼 Professional Summary")
use_ai = st.checkbox("Generate Summary using Gemini AI")
skills_input = st.text_area("List your Skills (comma-separated)")
experience_input = st.text_area("Describe your experience (comma-separated roles)")

summary = ""
if use_ai and st.button("Generate Summary"):
    summary = generate_summary(skills_input, experience_input)
else:
    summary = st.text_area("Write your Professional Summary", height=100)

st.header("🎓 Education")
if "education" not in st.session_state:
    st.session_state.education = []
with st.expander("Add Education"):
    degree = st.text_input("Degree")
    school = st.text_input("School/College")
    year = st.text_input("Year")
    if st.button("Add Education"):
        st.session_state.education.append({"degree": degree, "school": school, "year": year})

st.header("💼 Work Experience")
if "experience" not in st.session_state:
    st.session_state.experience = []
with st.expander("Add Experience"):
    role = st.text_input("Job Title")
    company = st.text_input("Company")
    duration = st.text_input("Duration")
    desc = st.text_area("Responsibilities")
    if st.button("Add Experience"):
        st.session_state.experience.append({"role": role, "company": company, "duration": duration, "desc": desc})

st.header("🚀 Projects")
if "projects" not in st.session_state:
    st.session_state.projects = []
with st.expander("Add Project"):
    title = st.text_input("Project Title")
    proj_desc = st.text_area("Project Description")
    if st.button("Add Project"):
        st.session_state.projects.append({"title": title, "desc": proj_desc})

st.header("🧠 Skills & More")
skills = [s.strip() for s in st.text_area("Technical Skills").split(",") if s.strip()]
soft_skills = [s.strip() for s in st.text_area("Soft Skills").split(",") if s.strip()]
languages = [s.strip() for s in st.text_area("Languages").split(",") if s.strip()]
tools = [s.strip() for s in st.text_area("Tools & Technologies").split(",") if s.strip()]

# === Export Button ===
if st.button("📄 Export Resume as PDF"):
    data = {
        "name": name,
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "summary": summary,
        "education": st.session_state.education,
        "experience": st.session_state.experience,
        "projects": st.session_state.projects,
        "skills": skills,
        "soft_skills": soft_skills,
        "languages": languages,
        "tools": tools
    }
    pdf = export_to_pdf(data, template)
    st.download_button("📥 Download PDF", pdf, file_name=f"{name}_resume.pdf")

