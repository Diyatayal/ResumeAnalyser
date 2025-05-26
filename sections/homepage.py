import streamlit as st
import nltk
import spacy
nltk.download('stopwords')
nltk.download('punkt')
nlp = spacy.load('sections/models/en_core_web_sm/en_core_web_sm-2.3.1')
import sqlite3
import random
import time, datetime,re
import pyresparser.resume_parser
from pyresparser import ResumeParser
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
import io, random
import fitz
from streamlit_tags import st_tags
from PIL import Image
from Courses import ds_course, web_course, android_course, ios_course, uiux_course, resume_videos, interview_videos

def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)
            print(page)
        text = fake_file_handle.getvalue()

    # close open handles
    converter.close()
    fake_file_handle.close()
    return text


def show_pdf(file_path):
    doc = fitz.open(file_path)
    for page in doc:
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        st.image(img)


def course_recommender(course_list):
    st.subheader("**Courses & Certificates🎓 Recommendations**")
    c = 0
    rec_course = []
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 4)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course

def get_word_count(resume_text):
    doc = nlp(resume_text)
    return len([token.text for token in doc if token.is_alpha])

def extract_experience(resume_text):
    matches = re.findall(r'(?i)(\b(19|20)\d{2})', resume_text)
    years = sorted(set(int(m[0]) for m in matches))
    if len(years) >= 2:
        return max(years) - min(years)
    elif len(years) == 1:
        return datetime.now().year - years[0]
    return None

def extract_skills(resume_text):
    skills_db = [
        "python", "java", "c++", "sql", "machine learning", "deep learning", "data analysis",
        "nlp", "computer vision", "tensorflow", "keras", "pytorch", "excel", "power bi",
        "tableau", "communication", "teamwork", "leadership"
    ]
    return list({skill for skill in skills_db if skill.lower() in resume_text.lower()})

def analyze_resume(resume_text):
    score = 0
    suggestions = []

    # Word count score
    word_count = get_word_count(resume_text)
    if word_count < 100:
        suggestions.append("Your resume is too short. Add more content.")
    elif word_count > 1500:
        suggestions.append("Your resume is too long. Try to summarize it.")
    else:
        score += 20

    # Experience score
    exp_years = extract_experience(resume_text)
    if exp_years is None:
        suggestions.append("Couldn't detect your experience. Add timelines with years.")
    elif exp_years >= 5:
        score += 20
    elif exp_years >= 2:
        score += 10
    else:
        score += 5

    # Skills score
    skills_found = extract_skills(resume_text)
    if len(skills_found) >= 10:
        score += 30
    elif len(skills_found) >= 5:
        score += 15
    else:
        suggestions.append("Add more relevant technical and soft skills.")

    # Projects section
    if "project" in resume_text.lower():
        score += 10
    else:
        suggestions.append("Include your projects to showcase hands-on work.")

    # Achievements section
    if "achievement" in resume_text.lower():
        score += 10
    else:
        suggestions.append("Include achievements to demonstrate results and impact.")

    return {
        "score": min(score, 100),
        "word_count": word_count,
        "experience": exp_years if exp_years is not None else 0,
        "skills": skills_found,
        "suggestions": suggestions
        }

connection = sqlite3.connect("resume_parser.db",check_same_thread=False)
cursor = connection.cursor()


def insert_data(name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills, recommended_skills,
                courses):
    DB_table_name = 'user_data'
    insert_sql = f"INSERT INTO {DB_table_name} VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    rec_values = (
    name, email, str(res_score), timestamp, str(no_of_pages), reco_field, cand_level, skills, recommended_skills,
    courses)
    cursor.execute(insert_sql, rec_values)
    connection.commit()



def run():
    st.title("Smart Resume Analyser")
    img = Image.open('./Logo/SRA_Logo.jpg')
    img = img.resize((250, 250))
    st.image(img)


    # Create table
    DB_table_name = 'user_data'

    table_sql = f"""
                CREATE TABLE IF NOT EXISTS {DB_table_name} (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Name TEXT,
                Email_ID TEXT,
                resume_score TEXT NOT NULL,
                Timestamp TEXT NOT NULL,
                Page_no TEXT NOT NULL,
                Predicted_Field TEXT NOT NULL,
                User_level TEXT NOT NULL,
                Actual_skills TEXT NOT NULL,
                Recommended_skills TEXT NOT NULL,
                Recommended_courses TEXT NOT NULL
                );
                """

    cursor.execute(table_sql)
      
    uploaded_file = st.file_uploader("Choose your Resume", type=["pdf"])
    if uploaded_file is not None:
        # with st.spinner('Uploading your Resume....'):
        #     time.sleep(4)
        save_image_path = './Uploaded_Resumes/' + uploaded_file.name
        with open(save_image_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        show_pdf(save_image_path)

        original_spacy_load = spacy.load
        # Monkey patch only inside pyresparser
        pyresparser.resume_parser.spacy.load = lambda name: original_spacy_load("sections/models/en_core_web_sm/en_core_web_sm-2.3.1")
        
        resume_data = ResumeParser(save_image_path).get_extracted_data()
        if resume_data:
            ## Get the whole resume data
            resume_text = pdf_reader(save_image_path)

            st.header("**Resume Analysis**")
            st.success("Hello " + resume_data['name'])
            st.subheader("**Your Basic info**")
            try:
                st.text('Name: ' + resume_data['name'])
                st.text('Email: ' + resume_data['email'])
                st.text('Contact: ' + resume_data['mobile_number'])
                st.text('Resume pages: ' + str(resume_data['no_of_pages']))
            except:
                pass
            cand_level = ''
            if resume_data['no_of_pages'] == 1:
                cand_level = "Fresher"
                st.markdown('''<h4 style='text-align: left; color: #d73b5c;'>You are looking Fresher.</h4>''',
                            unsafe_allow_html=True)
            elif resume_data['no_of_pages'] == 2:
                cand_level = "Intermediate"
                st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',
                            unsafe_allow_html=True)
            elif resume_data['no_of_pages'] >= 3:
                cand_level = "Experienced"
                st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',
                            unsafe_allow_html=True)

            st.subheader("**Skills Recommendation💡**")
            ## Skill shows
            keywords = st_tags(label='### Skills that you have',
                                text='See our skills recommendation',
                                value=resume_data['skills'], key='1')

            ##  recommendation
            ds_keyword = ['tensorflow', 'keras', 'pytorch', 'machine learning', 'deep Learning', 'flask',
                            'streamlit']
            web_keyword = ['react', 'django', 'node jS', 'react js', 'php', 'laravel', 'magento', 'wordpress',
                            'javascript', 'angular js', 'c#', 'flask']
            android_keyword = ['android', 'android development', 'flutter', 'kotlin', 'xml', 'kivy']
            ios_keyword = ['ios', 'ios development', 'swift', 'cocoa', 'cocoa touch', 'xcode']
            uiux_keyword = ['ux', 'adobe xd', 'figma', 'zeplin', 'balsamiq', 'ui', 'prototyping', 'wireframes',
                            'storyframes', 'adobe photoshop', 'photoshop', 'editing', 'adobe illustrator',
                            'illustrator', 'adobe after effects', 'after effects', 'adobe premier pro',
                            'premier pro', 'adobe indesign', 'indesign', 'wireframe', 'solid', 'grasp',
                            'user research', 'user experience']

            recommended_skills = []
            reco_field = ''
            rec_course = ''
            ## Courses recommendation
            for i in resume_data['skills']:
                ## Data science recommendation
                if i.lower() in ds_keyword:
                    print(i.lower())
                    reco_field = 'Data Science'
                    st.success("** Our analysis says you are looking for Data Science Jobs.**")
                    recommended_skills = ['Data Visualization', 'Predictive Analysis', 'Statistical Modeling',
                                            'Data Mining', 'Clustering & Classification', 'Data Analytics',
                                            'Quantitative Analysis', 'Web Scraping', 'ML Algorithms', 'Keras',
                                            'Pytorch', 'Probability', 'Scikit-learn', 'Tensorflow', "Flask",
                                            'Streamlit']
                    
                    existing_skills = [skill.lower() for skill in resume_data['skills']]
                    missing_skills = [skill for skill in recommended_skills if skill.lower() not in existing_skills]

                    if missing_skills:
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                    text='Recommended skills generated from System',
                                                    value=missing_skills, key='2')

                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                        unsafe_allow_html=True)
                    rec_course = course_recommender(ds_course)
                    break

                ## Web development recommendation
                elif i.lower() in web_keyword:
                    print(i.lower())
                    reco_field = 'Web Development'
                    st.success("** Our analysis says you are looking for Web Development Jobs **")
                    recommended_skills = ['React', 'Django', 'Node JS', 'React JS', 'php', 'laravel', 'Magento',
                                            'wordpress', 'Javascript', 'Angular JS', 'c#', 'Flask', 'SDK']
                    
                    
                    existing_skills = [skill.lower() for skill in resume_data['skills']]
                    missing_skills = [skill for skill in recommended_skills if skill.lower() not in existing_skills]

                    if missing_skills:
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                    text='Recommended skills generated from System',
                                                    value=missing_skills, key='2')
                        
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                        unsafe_allow_html=True)
                    rec_course = course_recommender(web_course)
                    break

                ## Android App Development
                elif i.lower() in android_keyword:
                    print(i.lower())
                    reco_field = 'Android Development'
                    st.success("** Our analysis says you are looking for Android App Development Jobs **")
                    recommended_skills = ['Android', 'Android development', 'Flutter', 'Kotlin', 'XML', 'Java',
                                            'Kivy', 'GIT', 'SDK', 'SQLite']
                    recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                    text='Recommended skills generated from System',
                                                    value=recommended_skills, key='4')
                    
                    
                    existing_skills = [skill.lower() for skill in resume_data['skills']]
                    missing_skills = [skill for skill in recommended_skills if skill.lower() not in existing_skills]

                    if missing_skills:
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                    text='Recommended skills generated from System',
                                                    value=missing_skills, key='2')
                        
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                        unsafe_allow_html=True)
                    rec_course = course_recommender(android_course)
                    break

                ## IOS App Development
                elif i.lower() in ios_keyword:
                    print(i.lower())
                    reco_field = 'IOS Development'
                    st.success("** Our analysis says you are looking for IOS App Development Jobs **")
                    recommended_skills = ['IOS', 'IOS Development', 'Swift', 'Cocoa', 'Cocoa Touch', 'Xcode',
                                            'Objective-C', 'SQLite', 'Plist', 'StoreKit', "UI-Kit", 'AV Foundation',
                                            'Auto-Layout']
 
                    
                    existing_skills = [skill.lower() for skill in resume_data['skills']]
                    missing_skills = [skill for skill in recommended_skills if skill.lower() not in existing_skills]

                    if missing_skills:
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                    text='Recommended skills generated from System',
                                                    value=missing_skills, key='2')
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                        unsafe_allow_html=True)
                    rec_course = course_recommender(ios_course)
                    break

                ## Ui-UX Recommendation
                elif i.lower() in uiux_keyword:
                    print(i.lower())
                    reco_field = 'UI-UX Development'
                    st.success("** Our analysis says you are looking for UI-UX Development Jobs **")
                    recommended_skills = ['UI', 'User Experience', 'Adobe XD', 'Figma', 'Zeplin', 'Balsamiq',
                                            'Prototyping', 'Wireframes', 'Storyframes', 'Adobe Photoshop', 'Editing',
                                            'Illustrator', 'After Effects', 'Premier Pro', 'Indesign', 'Wireframe',
                                            'Solid', 'Grasp', 'User Research']
                    
                    
                    existing_skills = [skill.lower() for skill in resume_data['skills']]
                    missing_skills = [skill for skill in recommended_skills if skill.lower() not in existing_skills]

                    if missing_skills:
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                    text='Recommended skills generated from System',
                                                    value=missing_skills, key='2')
                        
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                        unsafe_allow_html=True)
                    rec_course = course_recommender(uiux_course)
                    break

            #
            ## Insert into table
            ts = time.time()
            cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
            cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
            timestamp = str(cur_date + '_' + cur_time)

            ### Resume writing recommendation
            st.subheader("**Resume Tips & Ideas💡**")
            st.subheader("📊 ATS Resume Score")
            analysis_result = analyze_resume(resume_text)

            st.markdown(f"""
                <div style="border:1px solid #ddd; padding: 20px; border-radius: 10px;">
                    <h3 style="color: #4CAF50;">Your ATS Score: {analysis_result['score']} / 100</h3>
                    <p><strong>Word Count:</strong> {analysis_result['word_count']}</p>
                    <p><strong>Years of Experience:</strong> {analysis_result['experience']}</p>
                    <p><strong>Detected Skills:</strong> {', '.join(analysis_result['skills'])}</p>
                </div>
            """, unsafe_allow_html=True)
            

            if analysis_result["suggestions"]:
                st.warning("💡 Suggestions to Improve Your Resume:")
                for suggestion in analysis_result["suggestions"]:
                    st.markdown(f"-{suggestion}")

            st.warning(
                "** Note: This score is calculated based on the content that you have added in your Resume. **")

            insert_data(resume_data['name'], resume_data['email'], str(analysis_result['score']), timestamp,
                        str(resume_data['no_of_pages']), reco_field, cand_level, str(resume_data['skills']),
                        str(recommended_skills), str(rec_course))

            ## Resume writing video
            st.header("**Bonus Video for Resume Writing Tips💡**")
            resume_vid = random.choice(resume_videos)
            # res_vid_title = fetch_yt_video(resume_vid)
            res_vid_title = "Suggested for you"
            st.subheader("✅ **" + res_vid_title + "**")
            st.video(resume_vid)

            ## Interview Preparation Video
            st.header("**Bonus Video for Interview👨 Tips💡**")
            interview_vid = random.choice(interview_videos)
            # int_vid_title = fetch_yt_video(interview_vid)
            int_vid_title = "Recommended"
            st.subheader("✅ **" + int_vid_title + "**")
            st.video(interview_vid)

            connection.commit()
        else:
            st.error('Something went wrong..')


# run()