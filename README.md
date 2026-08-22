# AI Resume Screening Agent

An intelligent, end-to-end AI agent that scores and ranks a batch of candidate resumes against a Job Description (JD). 

Developed for the **Junior AI Research Associate Selection Round** at Rooman Technologies.

---

## Features

- **Streamlit Web Application Dashboard**: A beautiful, interactive graphical user interface to drag-and-drop resumes, view live analysis, see candidate score breakdowns, inspect matched/missing skills with visual color badges, and review candidate rationales.
- **Multi-Format Parsing**: Automatically parses plain text (`.txt`), Adobe PDF (`.pdf`), and Microsoft Word (`.docx`) files.
- **Provider-Agnostic LLM Engine**: Native support for **Google Gemini (recommended)**, **OpenAI (GPT-4o)**, **Anthropic (Claude)**, and **Groq** APIs.
- **Deep Semantic Matching**: Uses advanced prompt engineering to evaluate candidates on skills match (identifying matched/missing skills), relevant years of experience, highest education level, and rigorous relevance scoring (0-100).
- **Structured Data Export**: Automatically saves ranked results in CSV and JSON formats, alongside a detailed formatted text report.
- **Offline Mock Mode**: Runs the entire pipeline and UI instantly without requiring any API keys or network connection—perfect for reviewing and demonstrating capability out-of-the-box.
- **Error Resilience**: Gracefully handles parsing failures and connection timeouts on individual resumes without failing the entire batch run.

---

## Project Structure

```text
resume-screener/
├── app.py                  # CLI Driver & main entry point
├── web_app.py              # Streamlit Web Dashboard App interface
├── screener.py             # Core LLM prompt and API orchestration
├── parser.py               # Text parsing logic (TXT, PDF, DOCX)
├── config.py               # API client loading and key validation
├── push_to_github.py       # Helper script to automate GitHub OAuth/Device flow & push repo
├── requirements.txt        # Project dependencies
├── .env.example            # Template for environment variables
├── sample_data/            # Sample assets for out-of-the-box evaluation
│   ├── job_description.txt # Junior AI Research Associate Job Description
│   └── resumes/            # 11 sample candidate resumes (.txt)
└── output/                 # Results generated after the batch run
    ├── ranked_candidates.csv
    ├── ranked_candidates.json
    └── screening_report.txt
```

---

## Setup and Installation

### 1. Clone or Copy the Repository
Navigate to your project directory.

### 2. Install Dependencies
Make sure you have Python 3.8+ installed. Run:
```bash
pip install -r requirements.txt
```

*Note: PDF parsing requires `pypdf`, DOCX parsing requires `python-docx`, and the UI dashboard requires `streamlit` and `pandas`.*

### 3. Configure API Keys
Create a `.env` file in the project root directory and add your API key:
```env
# Set at least one API key (Optional if running in Mock Mode)
GEMINI_API_KEY=your_gemini_api_key_here
# OR
OPENAI_API_KEY=your_openai_api_key_here
# OR
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```
*(A template file named `.env.example` is provided in the project root.)*

---

## Usage Guide

### Option A: Run the Streamlit Web App Dashboard (Recommended)
Launch the graphical dashboard:
```bash
streamlit run web_app.py
```
This opens a browser tab (typically at `http://localhost:8501`) where you can adjust the JD, upload custom resumes, select API providers, and view the visual analysis.

### Option B: Run the Command-Line Interface (CLI)
You can run the agent directly using the default sample dataset:
```bash
python app.py
```
To run in **Offline Mock Mode** (generating realistic candidate rankings without calling external APIs or charging keys):
```bash
python app.py --mock
```

#### Advanced CLI Flags
```bash
python app.py --jd path/to/job_description.txt --resumes path/to/resumes_folder --output path/to/save_results
```

- `--jd`: Path to the job description file (default: `sample_data/job_description.txt`).
- `--resumes`: Path to the folder containing resumes (default: `sample_data/resumes`).
- `--output`: Directory to save generated reports (default: `output`).

---

## Scoring Logic and Design Choices

### NLP Semantic Scoring vs Keyword Matching
Traditional ATS systems perform keyword matching (e.g. TF-IDF), which often penalizes strong candidates who use synonyms. This agent uses an LLM to evaluate the resume context:
- It understands that a candidate listing *"React/Next.js"* matches a requirement for *"Frontend development frameworks"*.
- It checks for **skills matched** and **skills missing** semantically.
- It computes a rigorous **0-100 score**:
  - **80-100**: Excellent matches (strong Python/AI skills, hands-on experience, relevant education).
  - **50-79**: Medium matches (general software engineers or junior devs with some Python but lacking AI/agent experience).
  - **<50**: Unrelated profiles (completely different fields, e.g. mechanical engineers, recruiters).

### JSON Formatting Stability
LLMs are instructed to respond only with a raw structured JSON block. The code includes a robust cleanup layer using regular expressions (`clean_json_response`) to strip markdown tags (such as ````json ... ````) and extract the JSON payload, preventing parsing crashes.
