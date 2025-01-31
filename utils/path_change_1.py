import os
import re

# Define the root directory where your Gurobi code files are stored
root_dir = "/Users/stevenzhai/Desktop/MILP_data/sample-data-easy"

# Regular expressions to match the data load and solution save paths
data_load_pattern = re.compile(r'with open\("(\d+)/parameters.json", "r"\) as f:')
solution_save_pattern = re.compile(r"with open\('(\d+)_0/solution.json', 'w'\) as f:")

# Traverse the directory structure
for subdir, _, files in os.walk(root_dir):
    for file in files:
        if file == "optimus-code.py":
            # Check if the directory depth is greater than 2 to ensure it's in the desired subdirectory structure
            rel_path = os.path.relpath(subdir, root_dir)
            if len(rel_path.split(os.sep)) < 2:
                continue  # Skip files not in the deeper subdirectory structure

            # Construct the new directory prefix (e.g., "2/2_0")
            subdir_parts = rel_path.split(os.sep)
            new_prefix = f"{subdir_parts[0]}/{subdir_parts[1]}"

            # Read the file content
            file_path = os.path.join(subdir, file)
            with open(file_path, 'r') as f:
                content = f.read()

            # Replace the paths for loading data and saving solutions
            content = data_load_pattern.sub(f'with open("{new_prefix}/parameters.json", "r") as f:', content)
            content = solution_save_pattern.sub(f"with open('{new_prefix}/solution.json', 'w') as f:", content)

            # Write the modified content back to the file
            with open(file_path, 'w') as f:
                f.write(content)

            print(f"Updated {file_path}")
