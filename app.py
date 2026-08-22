import argparse
import csv
import json
import os
import sys
import random
import re
from config import Config
from parser import parse_resume
from screener import screen_single_resume

def setup_directories(output_dir):
    """Creates output directory if it doesn't exist."""
    os.makedirs(output_dir, exist_ok=True)

def load_text_file(file_path):
    """Loads text content from a file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Job Description file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def export_to_csv(data, output_path):
    """Exports ranked results to CSV."""
    keys = [
        "rank", "candidate_name", "relevance_score", "experience_years", 
        "education_level", "email", "phone", "skills_matched", "skills_missing", "reasoning", "file_name"
    ]
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for idx, row in enumerate(data):
            flat_row = row.copy()
            flat_row["rank"] = idx + 1
            # Convert lists to comma-separated strings
            flat_row["skills_matched"] = ", ".join(flat_row.get("skills_matched", []))
            flat_row["skills_missing"] = ", ".join(flat_row.get("skills_missing", []))
            writer.writerow(flat_row)

def export_to_json(data, output_path):
    """Exports ranked results to formatted JSON."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def export_text_report(data, jd, output_path):
    """Generates a text report summarizing the results."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("                     RESUME SCREENER AGENT REPORT\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total Candidates Screened: {len(data)}\n\n")
        
        f.write("RANKINGS SUMMARY:\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'Rank':<5}{'Candidate Name':<30}{'Score':<10}{'Experience (Yrs)':<20}{'Highest Education':<15}\n")
        f.write("-" * 80 + "\n")
        for idx, item in enumerate(data):
            f.write(
                f"{idx+1:<5}"
                f"{item['candidate_name'][:28]:<30}"
                f"{item['relevance_score']:<10}"
                f"{item.get('experience_years', 'N/A'):<20}"
                f"{str(item.get('education_level', 'N/A'))[:15]:<15}\n"
            )
        f.write("-" * 80 + "\n\n")
        
        f.write("CANDIDATE DETAIL ANALYSIS:\n")
        f.write("=" * 80 + "\n\n")
        for idx, item in enumerate(data):
            f.write(f"Rank {idx+1}: {item['candidate_name']}\n")
            f.write(f"  Score            : {item['relevance_score']}/100\n")
            f.write(f"  Email            : {item.get('email') or 'Not Found'}\n")
            f.write(f"  Phone            : {item.get('phone') or 'Not Found'}\n")
            f.write(f"  Experience       : {item.get('experience_years', 'N/A')} Years\n")
            f.write(f"  Education        : {item.get('education_level', 'N/A')}\n")
            f.write(f"  Skills Matched   : {', '.join(item.get('skills_matched', [])) or 'None'}\n")
            f.write(f"  Skills Missing   : {', '.join(item.get('skills_missing', [])) or 'None'}\n")
            f.write(f"  Source File      : {item.get('file_name')}\n")
            f.write(f"  Screening Notes  : {item.get('reasoning')}\n")
            f.write("-" * 80 + "\n\n")

def get_mock_result(filename, resume_text):
    """Generates a realistic mock screening result based on candidate profile."""
    name_match = re.search(r"^([^\n]+)", resume_text.strip())
    name = name_match.group(1).strip() if name_match else "Unknown Candidate"
    
    email_match = re.search(r"Email:\s*([^\n]+)", resume_text)
    email = email_match.group(1).strip() if email_match else None
    
    phone_match = re.search(r"Phone:\s*([^\n]+)", resume_text)
    phone = phone_match.group(1).strip() if phone_match else None

    # Default metrics based on filename keywords
    if "strong" in filename:
        score = random.randint(85, 98)
        exp = 1.0 + random.randint(0, 10)/10.0
        edu = "B.Tech Computer Science" if "aditya" in filename or "abhishek" in filename else "M.Sc. Data Science"
        matched = ["Python", "Git", "LLM APIs", "LangChain", "Prompt Engineering", "Vector Databases"]
        missing = ["PyTorch/TensorFlow"]
        reasoning = "Excellent candidate with clear hands-on experience building LLM-powered applications and vector search indexers. Strong programming and version control practices."
    elif "medium" in filename:
        score = random.randint(55, 75)
        exp = 2.0 if "rahul" in filename else 0.0
        edu = "B.E. Information Technology" if "rahul" in filename else "B.Tech CS (Cyber Security)"
        matched = ["Python", "Git", "SQL"]
        missing = ["LangChain", "Hugging Face", "LLM APIs", "Vector Databases"]
        reasoning = "Good software development foundations and Python knowledge, but lacks hands-on experience with LLM orchestration frameworks, vector databases, and prompt engineering."
    else:
        score = random.randint(15, 35)
        exp = 1.0
        edu = "MBA Human Resources" if "karan" in filename else "B.Tech Mechanical Engineering"
        matched = []
        missing = ["Python", "Git", "LLM APIs", "LangChain", "Hugging Face", "Vector Databases"]
        reasoning = "Unrelated candidate background. Profile shows no experience with software engineering, Python, Git, or AI/ML technologies."

    return {
        "candidate_name": name,
        "email": email,
        "phone": phone,
        "skills_matched": matched,
        "skills_missing": missing,
        "experience_years": exp,
        "education_level": edu,
        "relevance_score": score,
        "reasoning": reasoning
    }

def main():
    parser = argparse.ArgumentParser(
        description="AI Resume Screener CLI - Scores and ranks candidates against a Job Description."
    )
    parser.add_argument(
        "--jd", 
        default="sample_data/job_description.txt",
        help="Path to the Job Description file (default: sample_data/job_description.txt)"
    )
    parser.add_argument(
        "--resumes", 
        default="sample_data/resumes",
        help="Path to the resumes folder (default: sample_data/resumes)"
    )
    parser.add_argument(
        "--output", 
        default="output",
        help="Directory to save the ranked outputs (default: output)"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run in mock mode without calling external AI APIs (no credentials required)"
    )
    
    args = parser.parse_args()
    
    print("-" * 60)
    print("                RESUME SCREENING AGENT STARTING")
    print("-" * 60)
    
    # 1. Initialize API Config (if not running in mock mode)
    provider, client = None, None
    if not args.mock:
        try:
            provider, client = Config.get_client()
            print(f"[*] API initialized successfully using Provider: {provider.upper()}")
        except Exception as e:
            print(f"[!] Initialization Error: {e}")
            print("\n[TIP] You can run the agent in mock mode using the --mock flag:")
            print("      python app.py --mock")
            sys.exit(1)
    else:
        print("[*] Running in MOCK MODE (No LLM API calls will be charged/required)")
        
    # 2. Read Job Description
    try:
        jd_text = load_text_file(args.jd)
        print(f"[*] Loaded Job Description from {args.jd} ({len(jd_text)} characters)")
    except Exception as e:
        print(f"[!] Error loading Job Description: {e}")
        sys.exit(1)
        
    # 3. Scan Resumes Folder
    if not os.path.exists(args.resumes):
        print(f"[!] Resumes folder not found: {args.resumes}")
        sys.exit(1)
        
    files = [
        os.path.join(args.resumes, f) for f in os.listdir(args.resumes)
        if os.path.isfile(os.path.join(args.resumes, f)) and 
        os.path.splitext(f)[1].lower() in ('.pdf', '.docx', '.txt')
    ]
    
    if not files:
        print(f"[!] No valid resumes (.pdf, .docx, .txt) found in: {args.resumes}")
        sys.exit(1)
        
    print(f"[*] Found {len(files)} resumes to screen in {args.resumes}")
    print("-" * 60)
    
    # 4. Process each resume
    results = []
    for idx, filepath in enumerate(files):
        filename = os.path.basename(filepath)
        print(f"[{idx+1}/{len(files)}] Parsing {filename}...")
        try:
            resume_text = parse_resume(filepath)
            print(f"  -> Extracted {len(resume_text)} characters. Running screening AI...")
            
            if args.mock:
                result = get_mock_result(filename, resume_text)
            else:
                result = screen_single_resume(resume_text, jd_text, provider, client)
                
            # Add file path/source details
            result["file_name"] = filename
            results.append(result)
            print(f"  -> Evaluation Complete. Score: {result.get('relevance_score')}/100")
        except Exception as e:
            print(f"  -> [FAILED] parsing/evaluating {filename}: {e}")
            
    print("-" * 60)
    
    # 5. Sort candidates by score descending
    results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    
    # 6. Setup output directories
    setup_directories(args.output)
    csv_out = os.path.join(args.output, "ranked_candidates.csv")
    json_out = os.path.join(args.output, "ranked_candidates.json")
    report_out = os.path.join(args.output, "screening_report.txt")
    
    # 7. Export files
    print("[*] Exporting results...")
    export_to_csv(results, csv_out)
    print(f"  -> Saved CSV to: {csv_out}")
    export_to_json(results, json_out)
    print(f"  -> Saved JSON to: {json_out}")
    export_text_report(results, jd_text, report_out)
    print(f"  -> Saved report to: {report_out}")
    
    # 8. Print terminal summary table
    print("\nRANKED CANDIDATES SHORTLIST:")
    print("=" * 80)
    print(f"{'Rank':<5}{'Candidate Name':<30}{'Score':<10}{'Experience (Yrs)':<20}{'Education':<15}")
    print("=" * 80)
    for r_idx, item in enumerate(results):
        print(
            f"{r_idx+1:<5}"
            f"{item['candidate_name'][:28]:<30}"
            f"{item['relevance_score']:<10}"
            f"{item.get('experience_years', 'N/A'):<20}"
            f"{str(item.get('education_level', 'N/A'))[:15]:<15}"
        )
    print("=" * 80)
    print("\n[*] Batch resume screening process finished successfully!\n")

if __name__ == "__main__":
    main()
