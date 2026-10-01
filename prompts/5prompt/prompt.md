Check the official Rice University academic calendar / important dates and identify all events and deadlines scheduled for today (current calendar date) and the next 3 days (covering a 4-day window: today, today + 1 day, today + 2 days, and today + 3 days).

Save the results to a file named `events.json` in the root of this environment directory.

### Requirements:
1. The JSON file must contain an object mapping each date in the 4-day window (in `YYYY-MM-DD` format) to a list of event names (strings) occurring on that date.
2. The format for each event must be **just the event name**. If an event continues across multiple days, on each day it continues it must still be listed as **just the event name** (do not add words like "continues", "continued", "Day 2", etc.).
3. If no events or deadlines are scheduled for a specific date, map that date to an empty list `[]`.

### Example Format:
```json
{
  "2026-10-01": [],
  "2026-10-02": [
    "Families Weekend"
  ],
  "2026-10-03": [
    "Families Weekend"
  ],
  "2026-10-04": [
    "Families Weekend"
  ]
}
```
