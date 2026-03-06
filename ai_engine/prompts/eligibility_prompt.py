def eligibility_prompt(profile, grant):

    prompt = f"""
Check if the organization qualifies for this grant.

Grant Requirements:
{grant}

Organization Profile:
{profile}

Return JSON:

{{
 "eligibility": "Eligible or Not Eligible",
 "reason": "Explanation"
}}
"""
    return prompt