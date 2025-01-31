import os

# Directory to search (adjust this as necessary)
root_dir = "/Users/stevenzhai/Desktop/MILP_data/sample-data-easy"

# Dictionary to hold counts and file lists for each problem type
problem_dict = {}

# Walk through all files in the directory
for dirpath, dirnames, filenames in os.walk(root_dir):
    # Only proceed if the directory ends with "_c"
    if os.path.basename(dirpath).endswith("_c"):
        for filename in filenames:
            if filename == "optimus-code.py":
                file_path = os.path.join(dirpath, filename)
                
                # Read the file and find the problem type
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                    problem_type_line = None
                    for line in lines:
                        line = line.strip()
                        if line.startswith("# Problem type:"):
                            problem_type_line = line
                            break
                    
                    if problem_type_line:
                        # Extract the problem type
                        problem_type = problem_type_line.replace("# Problem type:", "").strip()
                        
                        # Update dictionary
                        if problem_type not in problem_dict:
                            problem_dict[problem_type] = []
                        problem_dict[problem_type].append(file_path)

# Print summary
for ptype, files in problem_dict.items():
    print(f"Problem Type: {ptype}")
    print(f"Count: {len(files)}")
    print("Instances:")
    for f in files:
        print(f"  - {f}")
    print()
