import json

def load_json_file(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)
