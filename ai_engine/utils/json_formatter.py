import json

def format_output(ai_response):

    try:
        data = json.loads(ai_response)
        return data
    except:
        return {"error": "Invalid JSON"}