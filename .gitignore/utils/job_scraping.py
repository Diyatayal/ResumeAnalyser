import streamlit as st
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Function to fetch job search results and get job_ids
def search_jobs(job_title, location):
    url = "https://jsearch.p.rapidapi.com/search"
    querystring = {
        "query": f"{job_title} in {location}",
        "page": "1",
        "num_pages": "1"
    }

    headers = {
        "x-rapidapi-key": os.getenv("RAPID_API_KEY"),
        "x-rapidapi-host": "jsearch.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    if response.status_code != 200:
        return [], f"Search Error: {response.status_code}"

    return response.json().get("data", []), None

# Function to fetch job details by job_id
def get_job_details(job_id):
    url = "https://jsearch.p.rapidapi.com/job-details"
    querystring = {
        "job_id": job_id,
        "country": "us"
    }

    headers = {
        "x-rapidapi-key": os.getenv("RAPID_API_KEY"),
        "x-rapidapi-host": "jsearch.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    if response.status_code != 200:
        return None

    data = response.json().get("data", [])
    return data[0] if data else None

# Streamlit UI
st.title("🔍Job Finder")

job_title = st.text_input("💼 Enter Job Title / Keyword", "Web Developer")
location = st.text_input("📍 Enter Location", "Remote")
## added page
if st.button("Search Jobs"):
    if not job_title:
        st.warning("Please ensure job title is provided.")
    else:
        with st.spinner("🔎 Searching for jobs..."):
            jobs, error = search_jobs(job_title, location)

            if error:
                st.error(error)
            elif not jobs:
                st.info("No jobs found.")
            else:
                st.success(f"Found {len(jobs)} jobs!")
                for job in jobs[:5]:
                    job_id = job.get("job_id")
                    detail = get_job_details(job_id)
                    if not detail:
                        # st.warning("⚠️ Failed to fetch job details for one of the jobs.")
                        continue
                    try:
                        st.subheader(detail.get("job_title", "N/A"))
                        st.markdown(f"**Company:** {detail.get('employer_name', 'N/A')}")
                        st.markdown(f"**Location:** {detail.get('job_location', 'N/A')}")
                        st.markdown(f"**Type:** {detail.get('job_employment_type', 'N/A')}")
                        
                        posted_ts = detail.get("job_posted_at_datetime_utc")
                        if posted_ts:
                            posted_date = datetime.strptime(posted_ts, "%Y-%m-%dT%H:%M:%S.%fZ")
                            st.markdown(f"**Posted:** {posted_date.strftime('%b %d, %Y')}")
                        else:
                            st.markdown("**Posted:** N/A")

                        apply_link = detail.get("job_apply_link", "#")
                        st.markdown(f"**Apply Link:** [Click here]({apply_link})")

                        desc = detail.get("job_description", "No description available.")
                        st.markdown("**Description:**")
                        st.write(desc[:500] + "...")
                        st.markdown("---")
                    except Exception as e:
                        # st.warning("⚠️ Error displaying one of the jobs.")
                        continue