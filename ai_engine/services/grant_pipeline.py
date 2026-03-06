import json
from services.grant_matcher import match_grants
from services.eligibility_checker import check_eligibility
from services.proposal_generator import generate_proposal


def run_grant_pipeline(profile, grants):

    results = []

    # Step 1: Find matching grants
    matches = match_grants(profile, grants)

    # For now we assume matches returns text
    # Later we will parse JSON

    for grant in grants:

        eligibility = check_eligibility(profile, grant)

        if "Eligible" in eligibility:

            proposal = generate_proposal(profile, grant)

            results.append({
                "grant_name": grant["grant_name"],
                "eligibility": eligibility,
                "proposal": proposal
            })

    return results