import re
import os
import glob

def transform_gurobi_code(input_code):
    """
    Transforms Gurobi model code by splitting each variable into two parts
    and updating the code accordingly.

    Parameters:
    - input_code (str): The original Gurobi code as a string.

    Returns:
    - str: The transformed Gurobi code.
    """
    # Step 1: Find variable declarations
    variable_pattern = re.compile(
        r'(# @Variable\s+)(\w+)\s+@Def:.*?@Shape:\s*(\[.*?\])\s*\n(\s*)(\w+)\s*=\s*model\.addVar(s?)\((.*?)\)',
        re.DOTALL
    )

    matches = list(variable_pattern.finditer(input_code))

    if not matches:
        print("No variable declarations found.")
        return input_code

    transformed_code = input_code
    var_replacements = {}

    def process_var_params(var_params, new_var_name):
        # Remove lb and ub parameters
        var_params = re.sub(r'\s*,?\s*lb\s*=\s*[^,]+', '', var_params)
        var_params = re.sub(r'\s*,?\s*ub\s*=\s*[^,]+', '', var_params)
        # Update the name parameter to new_var_name
        if 'name=' in var_params:
            var_params = re.sub(r'name\s*=\s*[^\s,]+', f'name="{new_var_name}"', var_params)
        else:
            var_params += f', name="{new_var_name}"'
        # Clean up any extra commas
        var_params = var_params.strip(', ')
        return var_params

    for match in matches:
        full_match = match.group(0)
        comment = match.group(1)
        var_name = match.group(2)
        shape = match.group(3).strip()
        indent = match.group(4)
        var_assignment = match.group(5)
        add_vars = match.group(6)
        var_params = match.group(7)

        # Remove the original variable declaration
        transformed_code = transformed_code.replace(full_match, '')

        # Create var1 and var2 declarations
        var1_name = var_name + '1'
        var2_name = var_name + '2'

        # Process var_params to remove lb/ub and update name
        var1_params = process_var_params(var_params, var1_name)
        var2_params = process_var_params(var_params, var2_name)

        # Update variable description
        var_description1 = f"Part 1 of variable {var_name}"
        var1_declaration = f"{comment}{var1_name} @Def: {var_description1} @Shape: {shape}\n{indent}{var1_name} = model.addVar{add_vars}({var1_params})\n"
        var_description2 = f"Part 2 of variable {var_name}"
        var2_declaration = f"{comment}{var2_name} @Def: {var_description2} @Shape: {shape}\n{indent}{var2_name} = model.addVar{add_vars}({var2_params})\n"

        # Add the new variable declarations at the end of the variables section
        variables_match = re.search(
            r'(# Variables\s*\n)(.*?)(?=\n#|$)', transformed_code, re.DOTALL
        )
        if variables_match:
            variables_section = variables_match.group(2)
            # Append var1 and var2 declarations at the end of variables section
            new_variables_section = variables_section + var1_declaration + var2_declaration
            # Replace the old variables section with the new one
            transformed_code = transformed_code.replace(variables_section, new_variables_section)
        else:
            # If variables section not found, prepend at the top
            transformed_code = var1_declaration + var2_declaration + transformed_code

        # Prepare variable replacement patterns
        if 's' in add_vars:
            # This is an array variable
            var_replacements[var_name] = f"({var1_name}[{{index}}] + {var2_name}[{{index}}])"
        else:
            # This is a scalar variable
            var_replacements[var_name] = f"({var1_name} + {var2_name})"

    # Build a regex pattern to match only the variable names we need to replace
    variable_names_pattern = '|'.join(map(re.escape, var_replacements.keys()))
    code_var_pattern = re.compile(r'\b(' + variable_names_pattern + r')\b\s*(\[[^\]]+\])?')

    # Function to replace variables in code
    def replace_var(match):
        var_name = match.group(1)
        index = match.group(2) or ''
        if var_name in var_replacements:
            replacement = var_replacements[var_name]
            if index:
                # Extract index content without brackets
                index_content = index.strip('[]')
                return replacement.format(index=index_content)
            else:
                return replacement
        else:
            return match.group(0)

    # Patterns to identify variable declarations and solution extraction lines
    variable_declaration_pattern = re.compile(r'^\s*\w+\s*=\s*model\.addVar[s]?\s*\(')
    solution_extraction_pattern = re.compile(r'\s*variables\[\s*\'\w+\'\s*\]\s*=')

    # Process the code line by line
    lines = transformed_code.split('\n')
    new_lines = []
    in_solution_block = False
    for line in lines:
        # Check if we're entering the solution extraction block
        if re.match(r'\s*# Extract solution', line):
            in_solution_block = True

        # Skip replacements in variable declarations and solution extraction
        if variable_declaration_pattern.match(line) or in_solution_block:
            new_lines.append(line)
        else:
            # Replace variables in this line
            new_line = code_var_pattern.sub(replace_var, line)
            new_lines.append(new_line)

        # Check if we're exiting the solution extraction block
        if in_solution_block and line.strip() == '':
            in_solution_block = False

    transformed_code = '\n'.join(new_lines)

    # Step 3: Update solution extraction code
    solution_block_match = re.search(r'(# Extract solution\b.*)', transformed_code, re.DOTALL)
    if solution_block_match:
        solution_block = solution_block_match.group(1)
        # Split the solution block into lines
        solution_lines = solution_block.split('\n')
        # Find the index of the line with 'variables = {}'
        variables_index = None
        for i, line in enumerate(solution_lines):
            if re.match(r'\s*variables\s*=\s*\{\}', line):
                variables_index = i
                break
        if variables_index is not None:
            # Prepare new assignments
            new_assignments = []
            indent_match = re.match(r'(\s*)', solution_lines[variables_index])
            base_indent = indent_match.group(1) if indent_match else ''
            assignment_indent = base_indent  # Assuming same indentation

            # Remove original variable assignments
            # Collect lines to keep
            lines_to_keep = solution_lines[:variables_index+1]
            # Remove lines that assign to the original variables
            pattern = re.compile(r'\s*variables\[\s*\'(' + '|'.join(var_replacements.keys()) + r')\'\s*\]\s*=\s*.*')
            for i in range(variables_index+1, len(solution_lines)):
                if not pattern.match(solution_lines[i]):
                    lines_to_keep.append(solution_lines[i])
            # Add assignments for new variables
            for var_name in var_replacements.keys():
                var1_name = var_name + '1'
                var2_name = var_name + '2'
                # Check if variable is array or scalar
                if '{index}' in var_replacements[var_name]:
                    # Variable with indices (array variable)
                    assignment1 = f"{assignment_indent}variables['{var1_name}'] = {{i: {var1_name}[i].X for i in {var1_name}.keys()}}"
                    assignment2 = f"{assignment_indent}variables['{var2_name}'] = {{i: {var2_name}[i].X for i in {var2_name}.keys()}}"
                else:
                    # Scalar variable
                    assignment1 = f"{assignment_indent}variables['{var1_name}'] = {var1_name}.X"
                    assignment2 = f"{assignment_indent}variables['{var2_name}'] = {var2_name}.X"
                new_assignments.extend([assignment1, assignment2])
            # Insert new assignments after 'variables = {}'
            solution_lines = lines_to_keep[:variables_index+1] + new_assignments + lines_to_keep[variables_index+1:]
            # Reconstruct the solution block
            solution_block_new = '\n'.join(solution_lines)
            # Replace the old solution block with the new one
            transformed_code = transformed_code.replace(solution_block, solution_block_new)
        else:
            print("'variables = {}' line not found in solution extraction block.")
    else:
        print("Solution extraction block not found.")

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
    transformed_code = transform_gurobi_code(input_code)

    # Write the transformed code to the output file
    with open(output_filepath, 'w') as f:
        f.write(transformed_code)

    print(f"Successfully wrote transformed code to {output_filepath}")

def process_all_optimus_code_files():
    """
    Processes all optimus-code.py files in directories ending with '_8'
    and outputs the transformed files to corresponding directories ending with '_6'.
    """
    input_files = glob.glob('/Users/stevenzhai/Desktop/MILP_data/sample-data-easy/*/*_c/optimus-code.py')
    for input_file in input_files:
        # Get the directory of the input file
        input_dir = os.path.dirname(input_file)
        # Replace '_8' with '_6' in the directory name
        output_dir = input_dir.replace('_c', '_h')
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)
        # Construct the output file path
        output_file = os.path.join(output_dir, os.path.basename(input_file))
        # Process the file
        transform_file(input_file, output_file)

if __name__ == "__main__":
    process_all_optimus_code_files()
