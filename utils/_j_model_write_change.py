import os
import re

root_dir = "/Users/stevenzhai/Desktop/MILP_data/sample-data-easy"

pattern = r'(model\.write\s*\(\s*")[^"]+(")'

# We'll define a function for replacement:
def replacer(match, new_path):
    # match.group(1) is the part up to (and including) the first quote
    # match.group(2) is the closing quote
    return f'{match.group(1)}{new_path}{match.group(2)}'

for dirpath, dirnames, filenames in os.walk(root_dir):
    # Only process directories that have "_k" in the folder name
    if "_k" in os.path.basename(dirpath):
        for filename in filenames:
            if filename == "optimus-code.py":
                python_file_path = os.path.join(dirpath, filename)
                
                # Read the file
                with open(python_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Figure out the correct path relative to root_dir
                relative_path = os.path.relpath(dirpath, root_dir)
                # Example result: "265/265_k"
                
                # Construct the new model-write path, e.g. "265/265_k/model.lp"
                new_model_write_path = f"{relative_path}/model.lp"

                # Use a function-based replacement so Python won't interpret
                # backslashes in new_model_write_path as group references.
                new_content = re.sub(
                    pattern, 
                    lambda m: replacer(m, new_model_write_path), 
                    content
                )

                # Write the file back if changes were made
                if new_content != content:
                    with open(python_file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Fixed model.write path in: {python_file_path}")
                else:
                    print(f"No change needed in: {python_file_path}")
