import json

# with open("testfile.json", "w", encoding="utf-8") as file:
#     json.dump(text, file, ensure_ascii=False, indent=4)

with open("testfile.json", "r") as file:
    data = json.load(file)

print(data["all_exes"][0])
