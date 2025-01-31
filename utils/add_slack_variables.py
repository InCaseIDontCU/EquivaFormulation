import json
import os
import re

def modify_problem_info_json(json_data):
    """
    Modifies the JSON data by adding slack variables to inequality constraints.

    Parameters:
    - json_data (dict): The original problem_info JSON data.

    Returns:
    - dict: The modified JSON data with slack variables added.
    """
    # Initialize a counter for slack variables to ensure unique names
    slack_counter = 0

    # Get the list of constraints
    constraints = json_data.get('constraints', [])

    # List to hold new constraints after modification
    new_constraints = []

    # Iterate over the constraints to find inequality constraints
    for constraint in constraints:
        description = constraint.get('description', '')
        formulation = constraint.get('formulation', '')
        code_dict = constraint.get('code', {})
        gurobipy_code = code_dict.get('gurobipy', '')

        # Check if the constraint is an inequality
        if '<=' in gurobipy_code or '>=' in gurobipy_code:
            # Determine the type of inequality
            if '<=' in gurobipy_code:
                inequality = '<='
            elif '>=' in gurobipy_code:
                inequality = '>='
            else:
                continue  # Not an inequality constraint

            # Split the gurobipy code into left-hand side (LHS) and right-hand side (RHS)
            lhs_rhs = re.split(r'<=|>=', gurobipy_code)
            if len(lhs_rhs) != 2:
                # Could not parse constraint; skip processing
                new_constraints.append(constraint)
                continue

            lhs = lhs_rhs[0].strip()
            rhs = lhs_rhs[1].strip()

            # Generate a unique slack variable name
            slack_var_name = f'slack_{slack_counter}'
            slack_counter += 1

            # Add the slack variable to the variables section
            if slack_var_name not in json_data['variables']:
                json_data['variables'][slack_var_name] = {
                    'description': f'Slack variable for constraint: {description}',
                    'type': 'continuous',
                    'shape': []
                }

            # Modify the constraint to include the slack variable
            if inequality == '<=':
                new_gurobipy_code = f"{lhs} + {slack_var_name} == {rhs}"
                new_formulation = f"{lhs} + {slack_var_name} = {rhs}"
            else:  # '>='
                new_gurobipy_code = f"{lhs} - {slack_var_name} == {rhs}"
                new_formulation = f"{lhs} - {slack_var_name} = {rhs}"

            # Update the constraint
            constraint['description'] = description + f" (Modified to include slack variable {slack_var_name})"
            constraint['formulation'] = new_formulation
            constraint['code']['gurobipy'] = f"model.addConstr({new_gurobipy_code})"

            new_constraints.append(constraint)
        else:
            # Not an inequality constraint; keep as is
            new_constraints.append(constraint)

    # Update the constraints in the JSON data
    json_data['constraints'] = new_constraints

    return json_data

def process_problem_info_file(input_filepath, output_filepath):
    """
    Processes a single problem_info.json file: modifies it and writes the output to the specified path.

    Parameters:
    - input_filepath (str): Path to the input problem_info.json file.
    - output_filepath (str): Path to the output problem_info.json file.
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

    # Initialize variables section if it doesn't exist
    if 'variables' not in json_data:
        json_data['variables'] = {}

    # Modify the JSON data
    modified_json_data = modify_problem_info_json(json_data)

    # Write the modified JSON to the output file
    try:
        with open(output_filepath, 'w') as outfile:
            json.dump(modified_json_data, outfile, indent=4)
        print(f"Successfully wrote modified JSON to {output_filepath}")
    except Exception as e:
        print(f"Failed to write modified JSON to {output_filepath}: {e}")

def main():
    # Example usage
    # Define the input and output file paths
    input_filepath = '/Users/stevenzhai/Desktop/MILP_data/sample-data-easy/1/1_8/problem_info.json'
    output_filepath = '/Users/stevenzhai/Desktop/MILP_data/sample-data-easy/1/1_7/problem_info.json'

    # Process the file
    process_problem_info_file(input_filepath, output_filepath)

if __name__ == "__main__":
    main()
