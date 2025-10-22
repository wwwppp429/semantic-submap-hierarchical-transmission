import json, sys
from jsonschema import Draft7Validator

def main(schema_path, json_path):
    schema = json.load(open(schema_path))
    data = json.load(open(json_path))
    v = Draft7Validator(schema)
    errors = sorted(v.iter_errors(data), key=lambda e: e.path)
    if errors:
        for e in errors:
            print(f"[ERROR] {list(e.path)}: {e.message}")
        sys.exit(1)
    print("OK:", json_path)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python validate_json.py <schema> <json>"); sys.exit(2)
    main(sys.argv[1], sys.argv[2])
