def grant_matching_prompt(profile, grants):

    prompt = f"""
You are an expert grant advisor.

Organization Profile:
{profile}

Available Grants:
{grants}

Task:
Find the top 3 most suitable grants.

Return:
- Grant Name
- Matching Score (0-100)
- Reason for match

Return response as JSON.
"""

    return prompt