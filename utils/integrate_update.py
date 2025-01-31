import os
import re

# Define the base directory where the files are located
base_dir = "/Users/stevenzhai/Desktop/MILP_data/sample-data-easy"

# Function to update the specified line in the optimus-code.py files
def update_optimus_code(base_dir):
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file == "optimus-code.py" and "_i" in root:
                file_path = os.path.join(root, file)

                # Read the contents of the file
                with open(file_path, "r") as f:
                    lines = f.readlines()

                # Update the specific line
                updated_lines = []
                for line in lines:
                    if re.search(r"solution\['objective'\] = model\.objVal", line):
                        updated_lines.append(line.replace("model.objVal", "10*model.objVal"))
                    else:
                        updated_lines.append(line)

                # Write the updated lines back to the file
                with open(file_path, "w") as f:
                    f.writelines(updated_lines)

                print(f"Updated: {file_path}")

# Run the update function
update_optimus_code(base_dir)
