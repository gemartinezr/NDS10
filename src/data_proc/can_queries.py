import re
from collections import defaultdict

# File path to your candump log
LOG_FILE = "canlog.txt"

# Dictionaries to store PID counts
pid_requests = defaultdict(int)
pid_responses = defaultdict(int)

# Regular expressions
request_re = re.compile(r'can0\s+7DF\s+\[8\]\s+\S+\s+\S+\s+([0-9A-Fa-f]{2})')
response_re = re.compile(r'can0\s+7E[89A-Fa-f]\s+\[8\]\s+\S+\s+([0-9A-Fa-f]{2})\s+([0-9A-Fa-f]{2})')

with open(LOG_FILE) as f:
    for line in f:
        request_match = request_re.search(line)
        if request_match:
            pid = request_match.group(1).upper()
            pid_requests[pid] += 1

        response_match = response_re.search(line)
        if response_match:
            pid = response_match.group(2).upper()  # Get actual PID from third byte
            pid_responses[pid] += 1

# Display results
print("=== PID REQUESTS (from 0x7DF) ===")
for pid, count in sorted(pid_requests.items()):
    print(f"PID 0x{pid}: {count} times")

print("\n=== PID RESPONSES (from 0x7E8 - 0x7EF) ===")
for pid, count in sorted(pid_responses.items()):
    print(f"PID 0x{pid}: {count} times")