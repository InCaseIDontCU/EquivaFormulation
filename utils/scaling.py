import json
import re
import os

def replace_variables_formulation(text, var_replacements):
    """
    Replaces variables in LaTeX formulations.
    """
    def replace_var(match):
        var_name = match.group(1)
        index = match.group(2) or ''
        if var_name in var_replacements:
            replacement = var_replacements[var_name]['formulation']
            if index:
                # Keep the index in the replacement
                return replacement + '_{' + index + '}'
            else:
                return replacement
        else:
            return match.group(0)

    # Pattern to match LaTeX variables with optional subscripts: a_i, a_{i,j}, etc.
    pattern = re.compile(r'\\?([a-zA-Z][a-zA-Z0-9]*)\s*(?:_\{?([^{}\s]+)\}?)?')

    return pattern.sub(replace_var, text)

def replace_variables_code(text, var_replacements):
    """
    Replaces variables in code.
    """
    def replace_var(match):
        var_name = match.group(1)
        index = match.group(2) or ''
        if var_name in var_replacements:
            replacement = var_replacements[var_name]['code']
            if index:
                # Keep the index in the replacement
                return replacement + index
            else:
                return replacement
        else:
            return match.group(0)

    # Pattern to match code variables with optional indices: a[i], a[i][j], etc.
    pattern = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(\[[^\]]+\])?')

    return pattern.sub(replace_var, text)

def adjust_variables(json_data):
    """
    Adjusts continuous variables by dividing them by scaling factors.
    """
    variables = json_data['variables']
    # Get continuous variables in order
    continuous_vars = [(var_name, var_info) for var_name, var_info in variables.items() if var_info.get('type') == 'continuous']
    # Build mapping from variable names to scaling factors
    var_replacements = {}
    for idx, (var_name, var_info) in enumerate(continuous_vars):
        scaling_factor = 10 ** (idx + 1)
        # Update variable description
        original_description = var_info.get('description', '')
        var_info['description'] = f"{original_description} ({scaling_factor} times before)"
        # Build variable replacement
        var_replacements[var_name] = {
            'scaling_factor': scaling_factor,
            'formulation': f"\\frac{{1}}{{{scaling_factor}}} {var_name}",
            'code': f"(1/{scaling_factor}) * {var_name}"
        }
    
    # Only proceed with replacements if there are continuous variables
    if var_replacements:
        # Replace in constraints
        for constraint in json_data.get('constraints', []):
            # Replace in 'formulation'
            if 'formulation' in constraint:
                constraint['formulation'] = replace_variables_formulation(constraint['formulation'], var_replacements)
            # Replace in 'code'
            if 'code' in constraint:
                for code_lang, code_str in constraint['code'].items():
                    constraint['code'][code_lang] = replace_variables_code(code_str, var_replacements)
        # Replace in objective
        objective = json_data.get('objective', {})
        if 'formulation' in objective:
            objective['formulation'] = replace_variables_formulation(objective['formulation'], var_replacements)
        if 'code' in objective:
            for code_lang, code_str in objective['code'].items():
                objective['code'][code_lang] = replace_variables_code(code_str, var_replacements)
    
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
    modified_json_data = adjust_variables(json_data)

    # Write the modified JSON to the output file
    try:
        with open(output_filepath, 'w') as outfile:
            json.dump(modified_json_data, outfile, indent=4)
        print(f"Successfully wrote modified JSON to {output_filepath}")
    except Exception as e:
        print(f"Failed to write modified JSON to {output_filepath}: {e}")

def process_all_json_files(base_dir):
    """
    Processes all JSON files in the given directory structure.
    """
    for root, dirs, files in os.walk(base_dir):
        if 'problem_info.json' in files and root.endswith('_0'):
            input_filepath = os.path.join(root, 'problem_info.json')
            output_dir = root[:-2] + '_1'
            output_filepath = os.path.join(output_dir, 'problem_info.json')
            process_single_json(input_filepath, output_filepath)

if __name__ == "__main__":
    base_dir = '/Users/stevenzhai/Desktop/MILP_data/sample-data-easy'
    process_all_json_files(base_dir)