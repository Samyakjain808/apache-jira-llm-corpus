from __future__ import annotations
import argparse, json
from jsonschema import Draft202012Validator
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True, help="Path to JSONL file")
    ap.add_argument("--schema", required=True, help="Path to JSON schema")
    args = ap.parse_args()

    schema = json.loads(Path(args.schema).read_text("utf-8"))
    validator = Draft202012Validator(schema)

    errors = 0
    for i, line in enumerate(Path(args.path).read_text("utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        obj = json.loads(line)
        for err in validator.iter_errors(obj):
            print(f"[line {i}] {err.message}")
            errors += 1
    if errors == 0:
        print("OK: All records validate against schema")
    else:
        print(f"Validation finished with {errors} error(s)")


if __name__ == "__main__":
    main()
