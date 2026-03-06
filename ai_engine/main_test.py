# import json
# from services.grant_matcher import match_grants

# profile = json.load(open("ai_engine/data/sample_profile.json"))
# grants = json.load(open("ai_engine/data/sample_grants.json"))

# result = match_grants(profile, grants)

# print(result)



# import json
# from services.grant_matcher import match_grants
# from services.eligibility_checker import check_eligibility

# profile = json.load(open("ai_engine/data/sample_profile.json"))
# grants = json.load(open("ai_engine/data/sample_grants.json"))

# # Step 1: Match grants
# matches = match_grants(profile, grants)

# print("Grant Matches:")
# print(matches)

# # Step 2: Check eligibility for first grant
# result = check_eligibility(profile, grants[0])

# print("Eligibility Check:")
# print(result)











# import json

# from services.grant_matcher import match_grants
# from services.eligibility_checker import check_eligibility
# from services.proposal_generator import generate_proposal


# # Load test data
# profile = json.load(open("ai_engine/data/sample_profile.json"))
# grants = json.load(open("ai_engine/data/sample_grants.json"))


# print("\n----- STEP 1: MATCH GRANTS -----")
# matches = match_grants(profile, grants)
# print(matches)


# print("\n----- STEP 2: CHECK ELIGIBILITY -----")
# eligibility = check_eligibility(profile, grants[0])
# print(eligibility)


# print("\n----- STEP 3: GENERATE PROPOSAL -----")
# proposal = generate_proposal(profile, grants[0])
# print(proposal)




import json
from services.grant_pipeline import run_grant_pipeline

profile = json.load(open("ai_engine/data/sample_profile.json"))
grants = json.load(open("ai_engine/data/sample_grants.json"))

result = run_grant_pipeline(profile, grants)

print(result)