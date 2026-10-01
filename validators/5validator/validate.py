#!/usr/bin/env python3
import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from html.parser import HTMLParser

POSSIBLE_FILES = [
    "events.json",
    "calendar_events.json",
    "academic_calendar.json",
    "output.json",
    "schedule.json",
]

# Fallback ground truth for Rice University Fall 2026 test dates
STATIC_FALLBACK_GT = {
    "2026-10-01": [],
    "2026-10-02": [
        "Families Weekend",
        "Last day to withdraw from the university with a 40% refund of tuition",
    ],
    "2026-10-03": [
        "Families Weekend",
    ],
    "2026-10-04": [
        "Families Weekend",
    ],
}


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.rows = []
        self.current_row = []
        self.current_cell = []

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.in_table = True
        elif self.in_table and tag == "tr":
            self.in_row = True
            self.current_row = []
        elif self.in_row and tag in ("td", "th"):
            self.in_cell = True
            self.current_cell = []

    def handle_endtag(self, tag):
        if tag == "table":
            self.in_table = False
        elif tag == "tr" and self.in_row:
            self.in_row = False
            if self.current_row:
                self.rows.append(self.current_row)
        elif tag in ("td", "th") and self.in_cell:
            self.in_cell = False
            self.current_row.append(" ".join("".join(self.current_cell).split()))

    def handle_data(self, data):
        if self.in_cell:
            self.current_cell.append(data)


def parse_date_cell(text):
    text = re.sub(r"\(.*?\)", "", text).strip()
    m_range = re.search(r"([A-Za-z]+)\s+(\d{1,2})\s*-\s*(\d{1,2}),?\s+(\d{4})", text)
    if m_range:
        m_str, d1_str, d2_str, y_str = m_range.groups()
        dates = []
        for d in range(int(d1_str), int(d2_str) + 1):
            try:
                dt = datetime.strptime(f"{m_str} {d} {y_str}", "%B %d %Y")
                dates.append(dt.strftime("%Y-%m-%d"))
            except ValueError:
                pass
        return dates

    m_single = re.search(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", text)
    if m_single:
        month_str, day_str, year_str = m_single.group(1), m_single.group(2), m_single.group(3)
        try:
            dt = datetime.strptime(f"{month_str} {day_str} {year_str}", "%B %d %Y")
            return [dt.strftime("%Y-%m-%d")]
        except ValueError:
            pass
    return []


def clean_event_name(raw_name):
    cleaned = re.sub(r"^(?:deadline|registration|graduation deadline)\s*:\s*", "", raw_name.strip(), flags=re.IGNORECASE)
    return cleaned.strip()


def check_no_continuation_words(event_str):
    # Reject annotations indicating continuation, e.g. "Families Weekend (continues)" or "Families Weekend - Day 2"
    forbidden = [r"\bcontinues\b", r"\bcontinued\b", r"\bday\s*\d+\b", r"\(cont\w*\)"]
    for pattern in forbidden:
        if re.search(pattern, event_str, re.IGNORECASE):
            return False
    return True


def fetch_live_ground_truth(target_dates):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    gt = {d: [] for d in target_dates}
    today = datetime.now()
    year = today.year
    month = today.month

    slugs = []
    if month in (8, 9, 10, 11, 12):
        slugs = [f"fall-semester-{year}", f"fall-quadmester-{year}"]
    elif month in (1, 2, 3, 4, 5):
        slugs = [f"spring-semester-{year}", f"spring-quadmester-{year}", f"winter-quadmester-{year}"]
    else:
        slugs = [f"summer-semester-{year}", f"summer-quadmester-{year}"]

    fetched_any = False
    for slug in slugs:
        url = f"https://registrar.rice.edu/calendars/{slug}"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                parser = TableParser()
                parser.feed(resp.read().decode("utf-8"))
                for row in parser.rows:
                    if len(row) >= 2:
                        for d in parse_date_cell(row[0]):
                            if d in gt:
                                gt[d].append(clean_event_name(row[1]))
                fetched_any = True
        except Exception as e:
            print(f"Warning: could not fetch calendar from {url}: {e}", file=sys.stderr)

    # Check important dates for campus/academic calendar multi-day events like Families Weekend
    try:
        req_dates = urllib.request.Request("https://parents.rice.edu/important-dates", headers=headers)
        with urllib.request.urlopen(req_dates, timeout=10) as resp:
            text = resp.read().decode("utf-8")
            m_fam = re.search(r"Families Weekend[\s\S]*?October\s+(\d{1,2})\s*-\s*(\d{1,2}),?\s+(\d{4})", text, re.IGNORECASE)
            if m_fam:
                d1, d2, y = int(m_fam.group(1)), int(m_fam.group(2)), int(m_fam.group(3))
                for day in range(d1, d2 + 1):
                    key = f"{y}-10-{day:02d}"
                    if key in gt:
                        gt[key].append("Families Weekend")
                fetched_any = True
    except Exception:
        pass

    if not fetched_any:
        return None

    return gt


def normalize_date_key(key):
    if not isinstance(key, str):
        key = str(key)
    key = key.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y", "%A, %B %d, %Y"):
        try:
            return datetime.strptime(key, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    m = re.search(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", key)
    if m:
        try:
            return datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", "%B %d %Y").strftime("%Y-%m-%d")
        except ValueError:
            pass
    return key


def load_agent_output():
    for filename in POSSIBLE_FILES:
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return filename, data
            except Exception as e:
                print(f"Warning: failed to read {filename} as JSON: {e}", file=sys.stderr)
    return None, None


def event_matches(agent_str, expected_str):
    a = clean_event_name(agent_str).lower()
    e = clean_event_name(expected_str).lower()
    if "families weekend" in e:
        return "families weekend" in a or "family weekend" in a
    if "40%" in e:
        return "40%" in a and ("refund" in a or "withdraw" in a)
    stopwords = {"deadline", "the", "a", "an", "to", "of", "in", "and", "from", "with", "for", "on", "at"}
    e_words = set(re.findall(r"\w+", e)) - stopwords
    a_words = set(re.findall(r"\w+", a)) - stopwords
    if not e_words:
        return True
    overlap = len(e_words & a_words) / len(e_words)
    return overlap >= 0.5


def main():
    source_file, agent_raw = load_agent_output()
    if not source_file or agent_raw is None:
        print("Error: Could not find agent output file. Expected 'events.json' in current directory.")
        sys.exit(1)

    print(f"Loaded calendar output from: {source_file}")

    today = datetime.now()
    target_dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(4)]
    print(f"Evaluating 4-day window starting today ({today.strftime('%Y-%m-%d')}): {target_dates}")

    # Normalize agent keys
    agent_data = {}
    for k, v in agent_raw.items():
        norm_k = normalize_date_key(k)
        if isinstance(v, list):
            agent_data[norm_k] = [str(x).strip() for x in v]
        elif isinstance(v, str):
            agent_data[norm_k] = [v.strip()] if v.strip() else []
        elif v is None:
            agent_data[norm_k] = []
        else:
            agent_data[norm_k] = [str(v).strip()]

    # Validate that continuation words are not used (format must be just event name)
    for d, events in agent_data.items():
        for ev in events:
            if not check_no_continuation_words(ev):
                print(
                    f"Validation failed: Event '{ev}' on date '{d}' must be just the event name (do not append 'continues', 'Day 2', etc.)."
                )
                sys.exit(1)

    # Determine ground truth
    gt = None
    try:
        gt = fetch_live_ground_truth(target_dates)
    except Exception as e:
        print(f"Warning: live ground truth query encountered an error: {e}", file=sys.stderr)

    if not gt:
        print("Using static ground truth fallback for validation...")
        gt = {d: STATIC_FALLBACK_GT.get(d, []) for d in target_dates}

    mismatches = []
    missing_dates = []

    for d in target_dates:
        if d not in agent_data:
            missing_dates.append(d)
            continue

        agent_events = agent_data[d]
        expected_events = gt.get(d, [])

        if expected_events:
            has_match = any(
                any(event_matches(a_ev, exp) for exp in expected_events)
                for a_ev in agent_events
            )
            # Also allow empty if expected was purely campus-level event and student only looked at registrar or vice versa
            if not has_match:
                mismatches.append(
                    f"Date '{d}': Expected valid event matching {expected_events}. Agent reported: {agent_events}"
                )
        else:
            if agent_events:
                mismatches.append(
                    f"Date '{d}': Expected no events (empty list []), but agent reported: {agent_events}"
                )

    if missing_dates:
        print(f"Validation failed: Missing date(s) in {source_file}: {missing_dates}")
        sys.exit(1)

    if mismatches:
        print(f"Validation failed with {len(mismatches)} mismatch(es):")
        for m in mismatches:
            print(f"  - {m}")
        sys.exit(1)

    print("Validation passed: Rice academic calendar events verified successfully (properly formatted with event names).")
    sys.exit(0)


if __name__ == "__main__":
    main()
