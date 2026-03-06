from pathlib import Path
import os

from dotenv import load_dotenv
from google import genai

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH)

api_key = os.getenv("GEMINI_KEY")
if not api_key:
    raise ValueError(f"GEMINI_KEY not found in environment or {ENV_PATH}")

client = genai.Client(api_key=api_key)


def check_eligibility(profile, grant):

    prompt = f"""
You are a grant eligibility expert.

Grant Requirements:
{grant}

Organization Profile:
{profile}

Check if the organization qualifies.

Return ONLY JSON:

{{
 "grant_name": "",
 "eligibility": "Eligible or Not Eligible",
 "reason": ""
}}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text
