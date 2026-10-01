#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

ensure_dependencies() {
    # Check if python3 and required standard modules are functional
    if command -v python3 >/dev/null 2>&1; then
        if python3 -c "import json, sys, os, re" >/dev/null 2>&1; then
            if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
                if python3 -m pip --version >/dev/null 2>&1; then
                    python3 -m pip install -r "$SCRIPT_DIR/requirements.txt" --break-system-packages 2>/dev/null || python3 -m pip install -r "$SCRIPT_DIR/requirements.txt" >/dev/null 2>&1 || true
                    return 0
                fi
            else
                return 0
            fi
        fi
    fi

    echo "Installing required dependencies for validator..." >&2

    local SUDO=""
    if [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null 2>&1; then
        SUDO="sudo"
    fi

    if command -v apt-get >/dev/null 2>&1; then
        export DEBIAN_FRONTEND=noninteractive
        $SUDO apt-get update -y -q >/dev/null
        $SUDO apt-get install -y -q --no-install-recommends python3 ca-certificates curl python3-pip >/dev/null 2>&1 || \
        $SUDO apt-get install -y -q --no-install-recommends python3 ca-certificates curl >/dev/null 2>&1 || true
        if command -v update-ca-certificates >/dev/null 2>&1; then
            $SUDO update-ca-certificates >/dev/null 2>&1 || true
        fi
    elif command -v apk >/dev/null 2>&1; then
        $SUDO apk update >/dev/null
        $SUDO apk add --no-cache python3 ca-certificates curl py3-pip >/dev/null 2>&1 || \
        $SUDO apk add --no-cache python3 ca-certificates curl >/dev/null 2>&1 || true
        if command -v update-ca-certificates >/dev/null 2>&1; then
            $SUDO update-ca-certificates >/dev/null 2>&1 || true
        fi
    elif command -v dnf >/dev/null 2>&1; then
        $SUDO dnf install -y python3 ca-certificates curl python3-pip >/dev/null 2>&1 || \
        $SUDO dnf install -y python3 ca-certificates curl >/dev/null 2>&1 || true
    elif command -v yum >/dev/null 2>&1; then
        $SUDO yum install -y python3 ca-certificates curl python3-pip >/dev/null 2>&1 || \
        $SUDO yum install -y python3 ca-certificates curl >/dev/null 2>&1 || true
    elif command -v pacman >/dev/null 2>&1; then
        $SUDO pacman -Sy --noconfirm python ca-certificates curl python-pip >/dev/null 2>&1 || \
        $SUDO pacman -Sy --noconfirm python ca-certificates curl >/dev/null 2>&1 || true
    elif command -v zypper >/dev/null 2>&1; then
        $SUDO zypper --non-interactive install python3 ca-certificates curl python3-pip >/dev/null 2>&1 || \
        $SUDO zypper --non-interactive install python3 ca-certificates curl >/dev/null 2>&1 || true
    elif command -v brew >/dev/null 2>&1; then
        brew install python3 ca-certificates curl >/dev/null 2>&1 || true
    else
        echo "Warning: No supported package manager found to install dependencies automatically." >&2
    fi

    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        if python3 -m pip --version >/dev/null 2>&1; then
            python3 -m pip install -r "$SCRIPT_DIR/requirements.txt" --break-system-packages 2>/dev/null || python3 -m pip install -r "$SCRIPT_DIR/requirements.txt" >/dev/null 2>&1 || true
        fi
    fi

    if ! command -v python3 >/dev/null 2>&1; then
        echo "Error: python3 is required to run the validator and could not be installed." >&2
        exit 1
    fi
}

ensure_dependencies

if [ -f "$SCRIPT_DIR/validate.py" ]; then
    exec python3 "$SCRIPT_DIR/validate.py"
fi

# Fallback: run embedded Python validator if validate.py was not copied alongside verify.sh
exec python3 - << 'EOF'
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
EOF
