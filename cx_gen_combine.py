import sys
import json
import os

def read_json_lists(filenames):
    """Reads multiple JSON files and returns a list of lists."""
    lists = []
    for file_path in filenames:
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}")
            sys.exit(1)

        with open(file_path, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"Error: Failed to parse JSON in {file_path}")
                sys.exit(1)

            if not isinstance(data, list):
                print(f"Error: Expected a list in {file_path}, got {type(data).__name__}")
                sys.exit(1)

            lists.append(data)

    return lists

def combine_json_lists(lists_of_lists):
    """Flattens a list of lists into a single list."""
    combined = []
    for lst in lists_of_lists:
        combined.extend(lst)
    return combined

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python cx_gen_combine.py <output_file.json> <input1.json> [<input2.json> ...]")
        sys.exit(1)

    output_file = sys.argv[1]
    input_files = sys.argv[2:]

    json_lists = read_json_lists(input_files)
    combined = combine_json_lists(json_lists)

    with open(output_file, 'w') as f:
        json.dump(combined, f, indent=2)

    print(f"Combined {len(input_files)} file(s) into {output_file}, total {len(combined)} items.")
