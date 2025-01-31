import os
import shutil
import glob

def delete_specific_files_and_directories(directory):
    # Patterns to match with recursive search
    patterns = ["**/*_8_a", "**/*_8_b"]
    
    # Iterate through each pattern
    for pattern in patterns:
        # Find all matching files and directories recursively
        files_and_dirs = glob.glob(os.path.join(directory, pattern), recursive=True)
        
        # Delete each matching file or directory
        for path in files_and_dirs:
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)  # Remove directory and all its contents
                else:
                    os.remove(path)
                print(f"Deleted: {path}")
            except OSError as e:
                print(f"Error deleting {path}: {e}")

# Usage example
directory = "/Users/stevenzhai/Desktop/MILP_data/sample-data-easy/"
delete_specific_files_and_directories(directory)