import os
import re

def update_optimus_code(directory_path):
    """
    Updates the paths in `optimus-code.py` files to replace `_f` with `_l`.

    Args:
        directory_path (str): The root directory containing the files.
    """
    for root, dirs, files in os.walk(directory_path):
        if "_i" in root:  # Check if the directory contains '_l'
            for file in files:
                if file == "optimus-code.py":
                    file_path = os.path.join(root, file)

                    # Read the file content
                    with open(file_path, 'r') as f:
                        content = f.read()

                    # Update the lines with the required substitution
                    updated_content = re.sub(
                        r'model\.write\("(\d+/\d+)_c/(model\.lp)"\)',
                        lambda match: f'model.write("{match.group(1)}_i/{match.group(2)}")',
                        content
                    )

                    # Write the updated content back to the file
                    with open(file_path, 'w') as f:
                        f.write(updated_content)

                    print(f"Updated: {file_path}")

# Example usage
root_directory = "/Users/stevenzhai/Desktop/MILP_data/sample-data-easy"
update_optimus_code(root_directory)
