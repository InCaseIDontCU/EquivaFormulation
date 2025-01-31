import os

# Define the root directory where your Gurobi code files are stored
root_dir = "/Users/stevenzhai/Desktop/MILP_data/sample-data-easy"

# Iterate through each file in the directory and subdirectories
for subdir, _, files in os.walk(root_dir):
    for file in files:
        if file == "optimus-code.py":  # Target only the specific Python files you want to modify
            file_path = os.path.join(subdir, file)
            
            # Open the file and read its contents
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Replace the absolute path for loading data
            content = content.replace(
                '"/Users/gaowenzhi/Desktop/optimus-OR-paper/data/new_dataset/sample_datasets/',
                '"'
            )
            
            # Replace the absolute path for outputting solutions
            content = content.replace(
                "'solution.json'",
                f"'{os.path.basename(subdir)}/solution.json'"
            )
            
            # Write the modified content back to the file
            with open(file_path, 'w') as f:
                f.write(content)
                
            print(f"Updated {file_path}")
