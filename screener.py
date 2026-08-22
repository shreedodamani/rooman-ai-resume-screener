import json
import os
import re
from config import Config
from parser import parse_resume

SYSTEM_PROMPT = """
You are an expert AI Resume Screener and Recruiter. Your task is to analyze the candidate's resume text against the provided Job Description (JD).
You must evaluate the candidate on:
1. Skills Match: Check which required and preferred skills are present, and which are missing.
2. Experience: Extract their years of relevant experience.
3. Education: Extract their highest level of education.
4. Score: Compute a relevance score from 0 to 100. Be honest and rigorous. A score of 80+ is for excellent matches, 50-80 for partial matches, and <50 for weak/unrelated matches.
5. Rationale: Provide a clear, professional explanation of the score, detailing the candidate's core strengths and gaps relative to the JD.

You MUST respond ONLY with a valid JSON object matching the following structure:
{
  "candidate_name": "Full Name of Candidate",
  "email": "email@example.com or null",
  "phone": "Phone number or null",
  "skills_matched": ["Skill A", "Skill B"],
  "skills_missing": ["Skill C"],
  "experience_years": 3.5,
  "education_level": "Bachelor's / Master's / PhD / etc.",
  "relevance_score": 85,
  "reasoning": "A concise summary of strengths and gaps."
}

Do not include any text before or after the JSON object. Do not include markdown code block formatting (like ```json). Just the raw JSON.
"""

def clean_json_response(text):
    """Cleans potential markdown wrapping and extracts the JSON substring."""
    cleaned = text.strip()
    # Remove markdown code block if present
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\n", "", cleaned)
        cleaned = re.sub(r"\n```$", "", cleaned)
    cleaned = cleaned.strip()
    
    # Try to find JSON block { ... } if there's other text
    match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
    if match:
        return match.group(1)
    return cleaned

def call_gemini(client, prompt):
    """Calls Gemini model."""
    # Support both new google-generativeai SDK style
    try:
        model = client.GenerativeModel(
            'gemini-1.5-flash',
            generation_config={"response_mime_type": "application/json"}
        )
    except:
        model = client.GenerativeModel('gemini-1.5-flash')
        
    response = model.generate_content([SYSTEM_PROMPT, prompt])
    return response.text

def call_openai(client, prompt, is_groq=False):
    """Calls OpenAI or Groq models."""
    model_name = "mixtral-8x7b-32768" if is_groq else "gpt-4o-mini"
    
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    return response.choices[0].message.content

def call_anthropic(client, prompt):
    """Calls Anthropic Claude model."""
    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=2000,
        temperature=0.1,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.content[0].text

def screen_single_resume(resume_text, job_description, provider, client):
    """Extracts information and scores a single resume against a job description."""
    user_prompt = f"### JOB DESCRIPTION:\n{job_description}\n\n### CANDIDATE RESUME:\n{resume_text}"
    
    try:
        if provider == "gemini":
            raw_response = call_gemini(client, user_prompt)
        elif provider in ("openai", "groq"):
            raw_response = call_openai(client, user_prompt, is_groq=(provider == "groq"))
        elif provider == "anthropic":
            raw_response = call_anthropic(client, user_prompt)
        else:
            raise ValueError(f"Unknown provider: {provider}")
        
        cleaned_response = clean_json_response(raw_response)
        parsed_data = json.loads(cleaned_response)
        return parsed_data
        
    except Exception as e:
        print(f"  [Error during LLM call]: {e}")
        # Return a fallback structured dictionary
        return {
            "candidate_name": "Error Parsing Candidate",
            "email": None,
            "phone": None,
            "skills_matched": [],
            "skills_missing": [],
            "experience_years": 0.0,
            "education_level": "Unknown",
            "relevance_score": 0,
            "reasoning": f"An error occurred during evaluation: {str(e)}"
        }
