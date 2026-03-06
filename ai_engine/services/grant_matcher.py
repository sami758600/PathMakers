from pathlib import Path
import os

from dotenv import load_dotenv
from google import genai
from utils.parser import parse_json

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH)

api_key = os.getenv("GEMINI_KEY")
if not api_key:
    raise ValueError(f"GEMINI_KEY not found in environment or {ENV_PATH}")

client = genai.Client(api_key=api_key)

def match_grants(profile, grants):

    prompt = f"""
    Organization Profile:
    {profile}

    Grants:
    {grants}

    Find the top 3 best grants and explain why.
    Return JSON.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text


# from utils.parser import parse_json

# response = client.models.generate_content(
#     model="gemini-2.5-flash",
#     contents=prompt
# )

# return parse_json(response.text)
