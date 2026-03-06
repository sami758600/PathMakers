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


def generate_proposal(profile, grant):

    prompt = f"""
Generate a professional grant proposal.

Organization Profile:
{profile}

Grant:
{grant}

Include sections:

1 Project Description
2 Problem Statement
3 Methodology
4 Expected Impact
5 Budget Summary
6 Timeline

Return structured text.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text
