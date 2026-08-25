import argparse
import os
from dotenv import load_dotenv

parser = argparse.ArgumentParser(description="Test automated images folder for compliance.")
args = parser.parse_args()

load_dotenv()

# PATH
path = os.getenv('AUTO_IMAGE_PATH', None)
if path is None:
    raise ValueError("AUTO_IMAGE_PATH environment variable not set.")

files_list = os.listdir(path)
files_list = [file for file in files_list if file not in ['.DS_Store'] and not ('Icon' in file and '.png' not in file)]
total_files = len(files_list)

# 1. TEST PREFIXES
prefix_list = ['BG', 'CUT']
for file in files_list:
    first_item = file.split('-')[0]
    if first_item not in prefix_list:
        print(f"ERROR (PREFIX): {file}")

# 2. TEST MATCHING ID'S WITH LAST NAME (SKIP NUMERIC IDS, EX: MLB ID)
for file in files_list:
    id = file.split('(')[1].split(')')[0].lower()
    name = file.split('-')[2].lower().replace("'", '')
    if id[0:2].isalpha() and id[0:2] != name[0:2]:
        print(f"WARNING (NAME/ID MISMATCH): {file} ----")

# 3. MAKE SURE EACH COMPONENT
components_dict = {}
for file in files_list:
    filename_splits = file.split('-', 1)
    prefix = filename_splits[0]
    suffix = filename_splits[1]
    current_components_for_suffix = components_dict.get(suffix, [])
    current_components_for_suffix.append(prefix)
    components_dict[suffix] = current_components_for_suffix

for player_file, components in components_dict.items():
    if len(components) != len(prefix_list):
        print(player_file, len(components), components)

print("TESTS COMPLETED")