import ijson
import re
from collections import defaultdict
from datetime import datetime

chunk_file = "C:/Users/makri/Desktop/SKILL AGEING/Posts_chunk_1.json"
tag_data = defaultdict(list)

print(f"📦 Streaming from {chunk_file}...\n")

processed = 0
tagged = 0

try:
    with open(chunk_file, "r", encoding="utf-8") as f:
        for i, post in enumerate(ijson.items(f, "item"), start=1):
            try:
                processed += 1
                post_id = post.get("Id", "N/A")
                post_type = post.get("PostTypeId", "?")
                date_str = post.get("CreationDate", "")
                score = int(post.get("Score", 0))
                views = int(post.get("ViewCount", 0))
                answers = int(post.get("AnswerCount", 0))
                tag_str = post.get("Tags", "")

                try:
                    date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f")
                except ValueError:
                    continue

                tags = re.findall(r'\|([^|]+)\|', tag_str) if tag_str else ["[untagged]"]

                for tag in tags:
                    tag_data[tag].append({
                        "date": date,
                        "score": score,
                        "views": views,
                        "answers": answers,
                        "type": post_type
                    })

                tagged += 1
                # Show a few debug entries
                if i <= 5 or i % 5000 == 0:
                    print(f"✅ Post {i} | ID: {post_id} | Type: {post_type} | Tags: {tags}")

            except Exception as e:
                print(f"⚠️ Skipped post {i} due to error: {e}")
                continue

except Exception as e:
    print(f"\n❌ Failed to process file: {e}")

print(f"\n✅ Finished processing {chunk_file}")
print(f"📊 Posts parsed: {processed}")
print(f"🏷 Tagged entries added: {tagged}")
print(f"🔍 Unique tags extracted: {len(tag_data)}")
