import json
import sys

"""
if len(sys.argv) < 2:
    print("Usage: python Tags.py <keyword>")
    sys.exit(1)

keyword = sys.argv[1].lower()
count = 0
dates = []
matches = []

with open("Posts.json", "r", encoding="utf-8") as file:
    for line in file:
        try:
            post = json.loads(line)
        except json.JSONDecodeError:
            continue  # skip malformed lines

        # Combine relevant fields to search
        content = (
            post.get("Body", "") +
            post.get("Title", "") +
            post.get("Tags", "")
        ).lower()

        if keyword in content:
            creation_date = post.get("CreationDate", "[No Date]")
            matches.append((post.get("Id"), creation_date))
            count += 1

        if "CreationDate" in post:
            dates.append(post["CreationDate"])

# Output
print(f"Total posts found containing '{keyword}': {count}")
for post_id, date in matches[:10]:  # preview first 10
    print(f"- Post ID: {post_id}, Date: {date}")

if dates:
    print(f"Total posts: {len(dates)}")
    print(f"Date range: {min(dates)} to {max(dates)}")
    
"""

import json
import sys

if len(sys.argv) < 2:
    print("Usage: python Tags.py <keyword>")
    sys.exit(1)

keyword = sys.argv[1].lower()
matches = []
dates = []
count = 0

with open("Posts.json", "r", encoding="utf-8") as file:
    for line_number, line in enumerate(file, start=1):
        try:
            post = json.loads(line)
        except json.JSONDecodeError:
            print(f"Warning: Skipping malformed line {line_number}")
            continue

        body = post.get("Body", "").lower()
        title = post.get("Title", "").lower()
        tags = post.get("Tags", "").lower()

        combined_text = f"{title} {body} {tags}"

        if keyword in combined_text:
            matches.append((post.get("Id", "N/A"), post.get("CreationDate", "N/A")))
            count += 1

        if "CreationDate" in post:
            dates.append(post["CreationDate"])

# Output
print(f"\n✅ Found {count} post(s) containing keyword: '{keyword}'")

for post_id, creation_date in matches[:10]:  # Only show first 10
    print(f"- Post ID: {post_id}, Created on: {creation_date}")

print(f"\n📅 Total posts scanned: {len(dates)}")
if dates:
    print(f"   Date range: {min(dates)} to {max(dates)}")
