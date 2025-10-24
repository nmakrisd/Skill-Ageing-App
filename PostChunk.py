input_file = "C:/Users/makri/Desktop/SKILL AGEING/Posts.json"
lines_per_file = 1000000
file_num = 1

with open(input_file, 'r', encoding='utf-8') as infile:
    while True:
        lines = list(infile.readline() for _ in range(lines_per_file))
        if not lines or lines[0] == '':
            break
        with open(f"Posts_chunk_{file_num}.json", 'w', encoding='utf-8') as chunk:
            chunk.writelines(lines)
        file_num += 1
        print(f"Created chunk: Posts_chunk_{file_num - 1}.json")