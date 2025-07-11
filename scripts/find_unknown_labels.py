import re
import json
from collections import Counter

def load_unknowns(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def print_unique_occurrences(unknowns):
    values = [u['value'] for u in unknowns]
    counts = Counter(values)
    print("Unique occurrences of unknown labels:")
    for val, cnt in counts.most_common():
        print(f"{cnt:4d}  -> {val}")

if __name__ == '__main__':
    json_path = 'unknown_labels.json'
    unknown_labels = load_unknowns(json_path)
    if not unknown_labels:
        print("Unknown labels were not found in the JSON file.")
    else:
        total = len(unknown_labels)
        uniques = len({u['value'] for u in unknown_labels})
        print(f"Total unknown labels found: {total}")
        print(f"Unique unknown labels: {uniques}")
        print_unique_occurrences(unknown_labels)