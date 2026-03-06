import json

def parse_json(response_text):

    try:
        return json.loads(response_text)
    except:
        return {"raw_output": response_text}