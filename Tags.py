import json
import ijson
import sys

if len(sys.argv) < 2:
    print("Usage: python Tags.py <keyword>")
    sys.exit(1)

keyword = sys.argv[1].lower()
matches = []
count = 0
dates = []

# Stream and process the file
with open("Posts.json", "r", encoding="utf-8") as file:
    posts = ijson.items(file, "posts.row.item")  # Navigate to the array

    for post in posts:
        count += 1
        body = (
            post.get("@Body", "") or
            post.get("@Title", "") or
            post.get("@Tags", "")
        ).lower()

        if keyword in body:
            creation_date = post.get("@CreationDate", "[No Date]")
            matches.append((post.get("@Id"), creation_date))

        date = post.get("@CreationDate")
        if date:
            dates.append(date)

# Output results
if matches:
    print(f"Found {len(matches)} post(s) containing '{keyword}':")
    for post_id, date in matches:
        print(f"- Post ID: {post_id}, Created on: {date}")
else:
    print(f"No posts found containing '{keyword}'.")

print(f"Total number of posts in the database: {count}")
if dates:
    print(f"Min date: {min(dates)}")
    print(f"Max date: {max(dates)}")