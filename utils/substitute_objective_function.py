import json
import os
import re

def extract_objective_components(objective_code):
    """
    Extracts the objective expression and optimization direction from the gurobipy code.
    Returns a tuple (expression, direction), where direction is 'MAXIMIZE' or 'MINIMIZE'.
    """
    # Pattern to match: model.setObjective(expression, GRB.MAXIMIZE) or GRB.MINIMIZE
    pattern = r'model\.setObjective\s*\(\s*(.+?)\s*,\s*GRB\.(MAXIMIZE|MINIMIZE)\s*\)'
    match = re.search(pattern, objective_code)
    if match:
        expression = match.group(1).strip()
        direction = match.group(2).strip()
        return expression, direction
    else:
        raise ValueError("Objective function format not recognized.")

def modify_json_data(json_data):
    """
    Modifies the JSON data by replacing the objective with variable zed and adding a constraint for zed.
    Returns the modified JSON data.
    """
    # Step 1: Extract the original objective function
    objective = json_data.get('objective', {})
    objective_code = objective.get('code', {}).get('gurobipy', '')
    
    try:
        original_expression, direction = extract_objective_components(objective_code)
    except ValueError as e:
        print(f"Error: {e}")
        return json_data  # Return unmodified if error occurs
    
    # Step 2: Add variable zed to the variables section
    if 'zed' not in json_data['variables']:
        json_data['variables']['zed'] = {
            'description': 'New variable representing the objective function',
            'type': 'continuous',
            'shape': []
        }
    else:
        print("Variable 'zed' already exists. Skipping addition.")
    
    # Step 3: Modify the objective to maximize or minimize zed based on original direction
    if direction == 'MAXIMIZE':
        new_direction = 'GRB.MAXIMIZE'
        new_formulation = 'Maximize \\ zed'
        new_description = 'Maximize the new variable zed.'
    elif direction == 'MINIMIZE':
        new_direction = 'GRB.MINIMIZE'
        new_formulation = 'Minimize \\ zed'
        new_description = 'Minimize the new variable zed.'
    else:
        # Default to maximize if direction is unrecognized
        new_direction = 'GRB.MAXIMIZE'
        new_formulation = 'Maximize \\ zed'
        new_description = 'Maximize the new variable zed.'
    
    json_data['objective'] = {
        'description': new_description,
        'formulation': new_formulation,
        'code': {
            'gurobipy': f'model.setObjective(zed, {new_direction})'
        }
    }
    
    # Step 4: Add constraint defining zed
    new_constraint = {
        'description': 'Constraint defining zed in terms of original variables.',
        'formulation': f'zed = {original_expression}',
        'code': {
            'gurobipy': f'model.addConstr(zed == {original_expression})'
        }
    }
    
    # Insert the new constraint at the beginning of the constraints list
    constraints = json_data.get('constraints', [])
    # Check if such a constraint already exists to avoid duplication
    existing_z_constraints = [
        c for c in constraints 
        if 'Constraint defining zed' in c.get('description', '')
    ]
    if not existing_z_constraints:
        constraints.insert(0, new_constraint)  # Insert at the beginning
    else:
        print("Constraint defining 'zed' already exists. Skipping addition.")
    json_data['constraints'] = constraints
    
    return json_data

def process_single_json(input_filepath, output_filepath):
    """
    Processes a single JSON file: modifies it and writes the output to the specified path.
    """
    # Ensure the output directory exists
    output_dir = os.path.dirname(output_filepath)
    os.makedirs(output_dir, exist_ok=True)
    
    # Load the JSON data
    try:
        with open(input_filepath, 'r') as infile:
            json_data = json.load(infile)
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON file {input_filepath}: {e}")
        return
    except FileNotFoundError:
        print(f"Input file {input_filepath} does not exist.")
        return
    
    # Modify the JSON data
    modified_json_data = modify_json_data(json_data)
    
    # Write the modified JSON to the output file
    try:
        with open(output_filepath, 'w') as outfile:
            json.dump(modified_json_data, outfile, indent=4)
        print(f"Successfully wrote modified JSON to {output_filepath}")
    except Exception as e:
        print(f"Failed to write modified JSON to {output_filepath}: {e}")

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
                input_filepath = os.path.join(input_dir, 'problem_info.json')
                output_filepath = os.path.join(output_dir, 'problem_info.json')
                process_single_json(input_filepath, output_filepath)
                
                print(f"Processed directory {input_dir}")
        
        # No need to recurse further into subdirectories
        # Uncomment the next line if you have nested '_8' directories
        # break  # Remove this line if you have nested directories

if __name__ == "__main__":
    main()
