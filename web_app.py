import streamlit as st
import pandas as pd
import json
import os
import re
from config import Config
from parser import parse_resume
from screener import screen_single_resume, get_mock_result

# Setup page configuration
st.set_page_config(
    page_title="AI Resume Screening Agent",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App branding headers
st.title("💼 AI Resume Screening Agent")
st.markdown("An intelligent recruitment assistant that extracts skills, education, and experience to rank candidates against a job specification.")
st.markdown("---")

# Sidebar Configuration
st.sidebar.header("⚙️ Configuration")

provider_option = st.sidebar.selectbox(
    "API Provider",
    ["Gemini (Recommended)", "OpenAI", "Anthropic", "Groq", "Mock Mode (Offline Demo)"]
)

provider_map = {
    "Gemini (Recommended)": "gemini",
    "OpenAI": "openai",
    "Anthropic": "anthropic",
    "Groq": "groq",
    "Mock Mode (Offline Demo)": "mock"
}

provider = provider_map[provider_option]

# API Key input
api_key = None
if provider != "mock":
    env_key = ""
    # Check config for existing env variables
    if provider == "gemini":
        env_key = Config.GEMINI_API_KEY or ""
    elif provider == "openai":
        env_key = Config.OPENAI_API_KEY or ""
    elif provider == "anthropic":
        env_key = Config.ANTHROPIC_API_KEY or ""
    elif provider == "groq":
        env_key = Config.GROQ_API_KEY or ""
        
    api_key_input = st.sidebar.text_input(
        f"{provider_option} API Key",
        value=env_key,
        type="password",
        help="Input your API key or set it in your local .env file."
    )
    
    if api_key_input:
        api_key = api_key_input
        # Update config class memory
        if provider == "gemini":
            Config.GEMINI_API_KEY = api_key
        elif provider == "openai":
            Config.OPENAI_API_KEY = api_key
        elif provider == "anthropic":
            Config.ANTHROPIC_API_KEY = api_key
        elif provider == "groq":
            Config.GROQ_API_KEY = api_key
    elif not env_key:
        st.sidebar.warning(f"⚠️ Please enter a {provider_option} API Key to continue.")

st.sidebar.markdown("""
### Ground Rules & Grading
- **Resume parsing**: Built-in support for `.txt`, `.pdf`, `.docx`.
- **Similarity scoring**: Semantic NLP analysis of experience, skills, and qualifications.
- **Batch limits**: Handles 10+ resumes efficiently.
""")

# Load default job description
default_jd = ""
jd_file = "sample_data/job_description.txt"
if os.path.exists(jd_file):
    with open(jd_file, "r", encoding="utf-8") as f:
        default_jd = f.read()

# Layout splits
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📋 Job Description (JD)")
    jd_input = st.text_area(
        "Enter the role specifications:",
        value=default_jd,
        height=320
    )

with col2:
    st.subheader("📂 Upload Resumes")
    uploaded_files = st.file_uploader(
        "Upload candidate resumes (PDF, DOCX, TXT):",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True
    )
    
    use_samples = st.checkbox("⚡ Use pre-loaded sample resumes (11 candidates)")
    
    if use_samples:
        st.info("💡 Loaded 11 default sample profiles representing strong, medium, weak, and unrelated candidates.")

# Trigger screening
if st.button("🚀 Run Screening Pipeline", use_container_width=True):
    resumes_to_screen = []
    
    # Check inputs
    if not jd_input:
        st.error("Please provide a Job Description.")
    elif not uploaded_files and not use_samples:
        st.error("Please upload resumes or check 'Use pre-loaded sample resumes'.")
    elif provider != "mock" and not api_key:
        st.error("Please configure your API key in the sidebar configuration.")
    else:
        # Load resumes
        if use_samples:
            sample_dir = "sample_data/resumes"
            if os.path.exists(sample_dir):
                for fname in os.listdir(sample_dir):
                    fpath = os.path.join(sample_dir, fname)
                    if os.path.isfile(fpath) and os.path.splitext(fname)[1].lower() in ('.pdf', '.docx', '.txt'):
                        try:
                            with open(fpath, "r", encoding="utf-8") as f:
                                resumes_to_screen.append({
                                    "filename": fname,
                                    "text": f.read()
                                })
                        except:
                            pass
        
        if uploaded_files:
            # We need to save uploaded files temporarily or pass bytes
            # Create a temp directory
            os.makedirs("temp_resumes", exist_ok=True)
            for f in uploaded_files:
                temp_path = os.path.join("temp_resumes", f.name)
                with open(temp_path, "wb") as temp_file:
                    temp_file.write(f.getbuffer())
                try:
                    text = parse_resume(temp_path)
                    resumes_to_screen.append({
                        "filename": f.name,
                        "text": text
                    })
                except Exception as e:
                    st.warning(f"Failed parsing {f.name}: {e}")
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                        
        if not resumes_to_screen:
            st.error("No valid resumes parsed. Check file formats.")
        else:
            # Setup client
            client_status = True
            client = None
            if provider != "mock":
                try:
                    _, client = Config.get_client()
                except Exception as e:
                    st.error(f"Failed to initialize API client: {e}")
                    client_status = False
                    
            if client_status:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                results = []
                for idx, item in enumerate(resumes_to_screen):
                    status_text.text(f"Screening candidate {idx+1}/{len(resumes_to_screen)}: {item['filename']}...")
                    try:
                        if provider == "mock":
                            result = get_mock_result(item['filename'], item['text'])
                        else:
                            result = screen_single_resume(item['text'], jd_input, provider, client)
                        result["file_name"] = item['filename']
                        results.append(result)
                    except Exception as e:
                        st.error(f"Error screening {item['filename']}: {e}")
                    progress_bar.progress((idx + 1) / len(resumes_to_screen))
                
                status_text.text("Screening completed! Formatting results...")
                
                # Sort descending
                results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
                
                st.session_state["screen_results"] = results
                st.success(f"Successfully screened {len(results)} candidates!")

# Display results if present
if "screen_results" in st.session_state and st.session_state["screen_results"]:
    results = st.session_state["screen_results"]
    
    st.markdown("---")
    st.header("📊 Ranked Candidate Shortlist")
    
    # Format table for presentation
    table_data = []
    for idx, item in enumerate(results):
        table_data.append({
            "Rank": idx + 1,
            "Candidate Name": item["candidate_name"],
            "Score": f"{item['relevance_score']}/100",
            "Experience": f"{item.get('experience_years', 'N/A')} Yrs",
            "Education": item.get("education_level", "Unknown"),
            "Email": item.get("email") or "N/A",
            "Phone": item.get("phone") or "N/A"
        })
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Export options
    csv_col, json_col, _ = st.columns([1, 1, 3])
    with csv_col:
        # Generate CSV bytes
        csv_df = pd.DataFrame(results)
        csv_data = csv_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download Shortlist (CSV)",
            data=csv_data,
            file_name="ranked_candidates.csv",
            mime="text/csv",
            use_container_width=True
        )
    with json_col:
        json_data = json.dumps(results, indent=2, ensure_ascii=False).encode('utf-8')
        st.download_button(
            "📥 Download Dataset (JSON)",
            data=json_data,
            file_name="ranked_candidates.json",
            mime="application/json",
            use_container_width=True
        )
        
    st.markdown("---")
    st.header("🔍 Candidate Deep-Dive Analysis")
    
    candidate_names = [item["candidate_name"] for item in results]
    selected_name = st.selectbox("Select a candidate to review detailed feedback:", candidate_names)
    
    # Find selected candidate details
    candidate = next(item for item in results if item["candidate_name"] == selected_name)
    
    col_metrics, col_details = st.columns([1, 2])
    
    with col_metrics:
        # Score metric with color coding
        score = candidate["relevance_score"]
        if score >= 80:
            st.markdown(f"<div style='border: 1px solid #4caf50; border-radius: 12px; padding: 20px; background-color: #e8f5e9; text-align: center;'><p style='margin: 0; color: #2e7d32; font-weight: bold;'>RELEVANCE SCORE</p><h1 style='margin: 0; color: #2e7d32; font-size: 4rem;'>{score}</h1><span style='color: #2e7d32; font-weight: bold;'>STRONG MATCH</span></div>", unsafe_allow_html=True)
        elif score >= 50:
            st.markdown(f"<div style='border: 1px solid #ff9800; border-radius: 12px; padding: 20px; background-color: #fff3e0; text-align: center;'><p style='margin: 0; color: #e65100; font-weight: bold;'>RELEVANCE SCORE</p><h1 style='margin: 0; color: #e65100; font-size: 4rem;'>{score}</h1><span style='color: #e65100; font-weight: bold;'>MEDIUM MATCH</span></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='border: 1px solid #f44336; border-radius: 12px; padding: 20px; background-color: #ffebee; text-align: center;'><p style='margin: 0; color: #c62828; font-weight: bold;'>RELEVANCE SCORE</p><h1 style='margin: 0; color: #c62828; font-size: 4rem;'>{score}</h1><span style='color: #c62828; font-weight: bold;'>WEAK MATCH</span></div>", unsafe_allow_html=True)
            
        st.markdown(f"**Experience:** {candidate.get('experience_years', 'N/A')} Years")
        st.markdown(f"**Highest Education:** {candidate.get('education_level', 'N/A')}")
        st.markdown(f"**Email:** {candidate.get('email') or 'N/A'}")
        st.markdown(f"**Phone:** {candidate.get('phone') or 'N/A'}")
        st.markdown(f"**Source File:** `{candidate.get('file_name')}`")
        
    with col_details:
        st.subheader("💡 AI Screening Rationale")
        st.info(candidate.get("reasoning", "No detailed reasoning provided."))
        
        # Display skills matched
        st.write("🟩 **Matched Skills:**")
        matched_skills = candidate.get("skills_matched", [])
        if matched_skills:
            badges_html = " ".join([f"<span style='display: inline-block; padding: 4px 10px; border-radius: 9999px; background-color: #c8e6c9; color: #256029; font-size: 13px; font-weight: bold; margin-bottom: 5px; margin-right: 5px;'>{skill}</span>" for skill in matched_skills])
            st.markdown(badges_html, unsafe_allow_html=True)
        else:
            st.write("No matching skills identified.")
            
        st.write("\n🟥 **Missing Skills:**")
        missing_skills = candidate.get("skills_missing", [])
        if missing_skills:
            badges_html = " ".join([f"<span style='display: inline-block; padding: 4px 10px; border-radius: 9999px; background-color: #ffcdd2; color: #8a1f1f; font-size: 13px; font-weight: bold; margin-bottom: 5px; margin-right: 5px;'>{skill}</span>" for skill in missing_skills])
            st.markdown(badges_html, unsafe_allow_html=True)
        else:
            st.write("No missing skills identified.")
