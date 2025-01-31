import re
import os

def transform_gurobi_code(input_code):
    """
    Transforms Gurobi model code by replacing the objective function
    with a variable zed, adding a constraint defining zed, and updating
    the solution extraction code to include zed.
    
    Parameters:
    - input_code (str): The original Gurobi code as a string.
    
    Returns:
    - str: The transformed Gurobi code.
    """
    # Step 1: Parse the code to find the objective function
    pattern = r'model\.setObjective\((.+?),\s*(GRB\.(MAXIMIZE|MINIMIZE))\)'
    matches = re.findall(pattern, input_code, re.DOTALL)
    
    if not matches:
        raise ValueError("Objective function not found or in unexpected format.")
    
    # Assume the last occurrence is the actual objective function
    original_objective, direction_full, direction = matches[-1]
    original_objective = original_objective.strip()
    direction_full = direction_full.strip()
    direction = direction.strip()
    
    # Step 2: Check if variable 'zed' already exists
    if re.search(r'\n\s*zed\s*=', input_code):
        print("Variable 'zed' already exists in the code. Skipping addition of variable 'zed'.")
        z_defined = True
    else:
        z_defined = False
    
    # Step 3: Replace the objective function with 'zed'
    transformed_code = re.sub(
        r'model\.setObjective\(.+?,\s*GRB\.(MAXIMIZE|MINIMIZE)\)',
        f'model.setObjective(zed, {direction_full})',
        input_code
    )
    
    # Step 4: Add the definition of 'zed' if not already defined
    if not z_defined:
        # Find the variables section
        variables_match = re.search(
            r'(# Variables\s+)((?:.|\n)*?)(# Constraints)', transformed_code, re.MULTILINE
        )
        if variables_match:
            variables_section = variables_match.group(2)
            # Add 'zed' variable definition at the end of variables section
            z_var_code = '\n# @Variable zed @Def: New variable representing the objective function @Shape: []\nzed = model.addVar(vtype=GRB.CONTINUOUS, name="zed")\n'
            new_variables_section = variables_section + z_var_code
            # Replace the old variables section with the new one
            transformed_code = transformed_code.replace(variables_section, new_variables_section)
        else:
            # If variables section not found, append at the end of variable declarations
            z_var_code = '\n# @Variable zed @Def: New variable representing the objective function @Shape: []\nz = model.addVar(vtype=GRB.CONTINUOUS, name="zed")\n'
            # Find last variable declaration
            last_var_match = re.search(r'(model\.addVar\(.*?\))', transformed_code, re.DOTALL | re.MULTILINE)
            if last_var_match:
                last_var = last_var_match.group(1)
                transformed_code = transformed_code.replace(
                    last_var,
                    last_var + z_var_code
                )
            else:
                # If no variable declarations found, add at the top
                transformed_code = z_var_code + transformed_code
    
    # Step 5: Add the constraint defining 'zed'
    z_constraint_code = f'\n# Constraint defining zed in terms of original variables\nmodel.addConstr(zed == {original_objective})\n'
    
    # Find where to insert the new constraint (at the end of constraints section)
    constraints_match = re.search(
        r'(# Constraints\s+)((?:.|\n)*?)(# Objective)', transformed_code, re.MULTILINE
    )
    if constraints_match:
        constraints_section = constraints_match.group(2)
        # Check if the constraint already exists
        if f'zed == {original_objective}' not in constraints_section:
            new_constraints_section = constraints_section + z_constraint_code
            # Replace the old constraints section with the new one
            transformed_code = transformed_code.replace(constraints_section, new_constraints_section)
        else:
            print("Constraint defining 'zed' already exists. Skipping addition.")
    else:
        # If constraints section not found, append at the end of the code
        transformed_code += z_constraint_code
    
    # Step 6: Add `variables['zed'] = zed.x` to the solution extraction code
    # New, simplified pattern to match variables block
    variables_block_pattern = r'(variables\s*=\s*\{\}\s*\n(?:\s*variables\[[^\]]+\]\s*=\s*.+\n)*)'
    variables_block_match = re.search(variables_block_pattern, transformed_code)

    # Debug information to help identify the block issue
    if variables_block_match:
        print("Variables assignment block found.")
        variables_block_full = variables_block_match.group(0)
        print(f"Matched variables block:\n{variables_block_full}")

        # Check if variables['zed'] = zed.x already exists
        if 'variables[\'zed\'] = zed.x' not in variables_block_full:
            new_assignment_line = 'variables[\'zed\'] = zed.x\n'  # Indented to match other assignments
            transformed_code = transformed_code.replace(variables_block_full, variables_block_full + new_assignment_line)
    else:
        print("Variables assignment block not found.")

    
    return transformed_code

def transform_file(input_filepath, output_filepath):
    """
    Reads the Gurobi code from input_filepath, transforms it,
    and writes the transformed code to output_filepath.
    """
    # Ensure the output directory exists
    output_dir = os.path.dirname(output_filepath)
    os.makedirs(output_dir, exist_ok=True)
    
    # Read the input code
    try:
        with open(input_filepath, 'r') as f:
            input_code = f.read()
    except FileNotFoundError:
        print(f"Input file {input_filepath} not found.")
        return
    
    # Transform the code
    try:
        transformed_code = transform_gurobi_code(input_code)
    except ValueError as e:
        print(f"Error during transformation: {e}")
        return
    
    # Write the transformed code to the output file
    with open(output_filepath, 'w') as f:
        f.write(transformed_code)
    
    print(f"Successfully wrote transformed code to {output_filepath}")


def main():
    # Define the base directory
    base_dir = '/Users/stevenzhai/Desktop/MILP_data/sample-data-easy'
    
    # Walk through the base directory
    for root, dirs, files in os.walk(base_dir):
        for dir_name in dirs:
            if dir_name.endswith('_c'):
                # Construct input and output directory paths
                input_dir = os.path.join(root, dir_name)
                output_dir = os.path.join(root, dir_name[:-1] + 'f')  # Replace '_8' with '_3'
                
                # Ensure the output directory exists
                os.makedirs(output_dir, exist_ok=True)
                
                # Process problem_info.json
                input_filepath = os.path.join(input_dir, 'optimus-code.py')
                output_filepath = os.path.join(output_dir, 'optimus-code.py')
                transform_file(input_filepath, output_filepath)
                
                print(f"Processed directory {input_dir}")
        
        # No need to recurse further into subdirectories
        # Uncomment the next line if you have nested '_8' directories
        # break  # Remove this line if you have nested directories

if __name__ == "__main__":
    main()
