def proposal_prompt(profile, grant):

    prompt = f"""
Generate a professional grant proposal.

Organization:
{profile}

Grant:
{grant}

Sections required:
1. Project Description
2. Problem Statement
3. Methodology
4. Expected Impact
5. Budget Summary
6. Timeline

Return structured text.
"""
    return prompt