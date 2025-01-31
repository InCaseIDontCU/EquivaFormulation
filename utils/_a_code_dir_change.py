import os

def modify_paths(file_path):
    # Read the original file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Get the directory name from the file path
    dir_name = os.path.dirname(file_path)
    sub_dir = os.path.basename(dir_name)
    parent_dir = os.path.basename(os.path.dirname(dir_name))
    
    # Replace the paths
    modified_content = content.replace(
        f'"{parent_dir}/parameters.json"',
        f'"{parent_dir}/{sub_dir}/parameters.json"'
    ).replace(
        f"'{parent_dir}/solution.json'",
        f"'{parent_dir}/{sub_dir}/solution.json'"
    )
    
    # Write the modified content back
    with open(file_path, 'w') as f:
        f.write(modified_content)

def process_directory(root_dir):
    for root, dirs, files in os.walk(root_dir):
        # Only process directories ending with '_a'
        if not root.endswith('_a'):
            continue
            
        for file in files:
            if file == 'optimus-code.py':
                file_path = os.path.join(root, file)
                print(f"Processing: {file_path}")  # Added for visibility
                modify_paths(file_path)

# Usage
root_directory = "/Users/stevenzhai/Desktop/MILP_data/sample-data-easy"
process_directory(root_directory)