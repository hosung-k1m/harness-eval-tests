#!/usr/bin/env python3
import json
import os
import re
import sys

GROUND_TRUTH = {
    1: {
        "canonical": "Doogie doogie ahh ma lalala",
        "valid_normalized": [
            "doogie doogie ahh ma lalala",
            "doogie doogie ah ma lalala",
        ],
    },
    2: {
        "canonical": "Dr. Strange",
        "valid_normalized": [
            "dr. strange",
            "dr strange",
            "doctor strange",
        ],
    },
    3: {
        "canonical": "Whole Milk",
        "valid_normalized": [
            "whole milk",
        ],
    },
}

POSSIBLE_FILES = [
    "answers.json",
    "answers.txt",
    "answers.md",
    "output.json",
    "result.json",
]


def normalize_text(val):
    if not isinstance(val, str):
        val = str(val)
    # Strip whitespace, quotes, markdown backticks
    val = val.strip().strip("'\"`").strip()
    # Strip leading prefixes like "1.", "1:", "1 -", "Answer 1:", "Q1:"
    val = re.sub(r'^(?:q(?:uestion)?\s*[1-3]|answer\s*[1-3]|[1-3])\s*[:.)\-]\s*', '', val, flags=re.IGNORECASE)
    val = val.strip().strip("'\"`").strip()
    # Strip trailing punctuation (. ! , ;)
    val = re.sub(r'[.,;!]+$', '', val).strip()
    # Collapse multiple whitespaces
    val = re.sub(r'\s+', ' ', val)
    return val.lower()


def parse_json_data(data):
    answers = {}
    if isinstance(data, dict):
        key_aliases = {
            1: ["1", 1, "q1", "q_1", "question1", "question_1", "question 1", "question one"],
            2: ["2", 2, "q2", "q_2", "question2", "question_2", "question 2", "question two"],
            3: ["3", 3, "q3", "q_3", "question3", "question_3", "question 3", "question three"],
        }
        for q_id, aliases in key_aliases.items():
            for alias in aliases:
                if alias in data:
                    answers[q_id] = str(data[alias])
                    break
    elif isinstance(data, list):
        if len(data) >= 3:
            for idx in range(3):
                answers[idx + 1] = str(data[idx])
    return answers


def parse_text_lines(text):
    answers = {}
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        m = re.match(r'^(?:q(?:uestion)?\s*([1-3])|answer\s*([1-3])|([1-3]))\s*[:.)\-]\s*(.+)$', line, re.IGNORECASE)
        if m:
            num = int(m.group(1) or m.group(2) or m.group(3))
            answers[num] = m.group(4).strip()

    if len(answers) < 3 and len(lines) >= 3:
        for idx in range(3):
            if (idx + 1) not in answers:
                answers[idx + 1] = lines[idx]
    return answers


def load_answers():
    for filename in POSSIBLE_FILES:
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if not content:
                    continue

                if filename.endswith(".json"):
                    try:
                        data = json.loads(content)
                        parsed = parse_json_data(data)
                        if parsed:
                            return filename, parsed
                    except json.JSONDecodeError:
                        pass

                # If JSON parsing was not applicable or failed, try line parsing
                parsed = parse_text_lines(content)
                if parsed:
                    return filename, parsed
            except Exception as e:
                print(f"Warning: could not read {filename}: {e}", file=sys.stderr)
    return None, {}


def main():
    source_file, answers = load_answers()

    if not source_file or not answers:
        print(f"Error: Could not find answers file. Expected 'answers.json' in the working directory.")
        sys.exit(1)

    print(f"Loaded answers from {source_file}: {answers}")

    mismatches = []
    for q_id, cfg in GROUND_TRUTH.items():
        if q_id not in answers:
            mismatches.append(f"Question {q_id}: missing answer")
            continue

        actual_raw = answers[q_id]
        actual_norm = normalize_text(actual_raw)
        canonical = cfg["canonical"]
        valid_norms = cfg["valid_normalized"]

        if actual_norm not in valid_norms:
            mismatches.append(
                f"Question {q_id}: expected '{canonical}', got '{actual_raw}'"
            )

    if mismatches:
        print(f"Validation failed with {len(mismatches)} mismatch(es):")
        for m in mismatches:
            print(f"  - {m}")
        sys.exit(1)

    print("Validation passed: All 3 questions answered correctly.")
    sys.exit(0)


if __name__ == "__main__":
    main()
