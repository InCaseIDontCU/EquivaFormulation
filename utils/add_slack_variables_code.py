import ast
import astor
import os
import re

class SlackVariableTransformer(ast.NodeTransformer):
    def __init__(self):
        self.slack_counter = 0
        self.slack_vars = []
        self.slack_var_assignments = []
        self.slack_var_extractions = []

    def visit_Call(self, node):
        # Check if the function call is model.addConstr or model.addConstrs
        if isinstance(node.func, ast.Attribute) and node.func.attr in ('addConstr', 'addConstrs'):
            # Process the constraint
            args = node.args
            if not args:
                return node  # No arguments, skip

            constraint_expr = args[0]
            new_constraint_expr = self.process_constraint_expr(constraint_expr)

            if new_constraint_expr is not None:
                args[0] = new_constraint_expr

                # Add slack variable definition
                # Slack variables will be added in the same scope as the model
                pass  # We will collect slack variable definitions separately

        return self.generic_visit(node)

    def process_constraint_expr(self, expr):
        if isinstance(expr, ast.Compare):
            # Handle inequality comparisons
            if len(expr.ops) != 1:
                return None  # Complex comparison, skip

            op = expr.ops[0]
            if isinstance(op, (ast.LtE, ast.GtE)):
                # Create a new slack variable
                slack_var_name = f'slack_{self.slack_counter}'
                self.slack_counter += 1

                # Define slack variable (lb=0)
                slack_var_def = ast.Assign(
                    targets=[ast.Name(id=slack_var_name, ctx=ast.Store())],
                    value=ast.Call(
                        func=ast.Attribute(value=ast.Name(id='model', ctx=ast.Load()), attr='addVar', ctx=ast.Load()),
                        args=[],
                        keywords=[
                            ast.keyword(arg='lb', value=ast.Num(n=0)),
                            ast.keyword(arg='name', value=ast.Str(s=slack_var_name))
                        ]
                    )
                )
                self.slack_vars.append(slack_var_def)

                # Modify the constraint expression
                if isinstance(op, ast.LtE):
                    # expr.left + slack_var == expr.comparators[0]
                    new_left = ast.BinOp(
                        left=expr.left,
                        op=ast.Add(),
                        right=ast.Name(id=slack_var_name, ctx=ast.Load())
                    )
                else:  # GtE
                    # expr.left - slack_var == expr.comparators[0]
                    new_left = ast.BinOp(
                        left=expr.left,
                        op=ast.Sub(),
                        right=ast.Name(id=slack_var_name, ctx=ast.Load())
                    )

                new_expr = ast.Compare(
                    left=new_left,
                    ops=[ast.Eq()],
                    comparators=expr.comparators
                )

                # Add slack variable extraction
                slack_var_extraction = ast.Assign(
                    targets=[ast.Subscript(
                        value=ast.Name(id='variables', ctx=ast.Load()),
                        slice=ast.Index(ast.Str(slack_var_name)),
                        ctx=ast.Store()
                    )],
                    value=ast.Attribute(
                        value=ast.Name(id=slack_var_name, ctx=ast.Load()),
                        attr='X',
                        ctx=ast.Load()
                    )
                )
                self.slack_var_extractions.append(slack_var_extraction)

                return new_expr

        return None  # Not an inequality constraint or unsupported format

def transform_gurobi_code_with_ast(input_code):
    """
    Transforms Gurobi model code by adding slack variables to all inequality constraints,
    using AST parsing.
    """
    # Parse the code into an AST
    tree = ast.parse(input_code)

    # Create a transformer and apply it to the AST
    transformer = SlackVariableTransformer()
    transformer.visit(tree)
    ast.fix_missing_locations(tree)

    # Reconstruct the code from the AST
    transformed_code = astor.to_source(tree)

    # Insert slack variable definitions after model creation
    model_creation_pattern = r'(model\s*=\s*Model\(\))'
    slack_vars_code = '\n'.join([astor.to_source(node).strip() for node in transformer.slack_vars])

    transformed_code = re.sub(
        model_creation_pattern,
        r'\1\n' + slack_vars_code,
        transformed_code
    )

    # Insert slack variable extractions before solution extraction
    variables_extraction_pattern = r'(variables\s*=\s*\{\})'
    slack_vars_extraction_code = '\n'.join([astor.to_source(node).strip() for node in transformer.slack_var_extractions])

    transformed_code = re.sub(
        variables_extraction_pattern,
        r'\1\n' + slack_vars_extraction_code,
        transformed_code
    )

    return transformed_code

def transform_file_with_ast(input_filepath, output_filepath):
    """
    Reads the Gurobi code from input_filepath, transforms it to add slack variables,
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
        transformed_code = transform_gurobi_code_with_ast(input_code)
    except Exception as e:
        print(f"Error during transformation: {e}")
        return
    
    # Write the transformed code to the output file
    with open(output_filepath, 'w') as f:
        f.write(transformed_code)
    
    print(f"Successfully wrote transformed code to {output_filepath}")


# Example usage
if __name__ == "__main__":
    input_filepath = '/Users/stevenzhai/Desktop/MILP_data/sample-data-easy/1/1_8/optimus-code.py'
    output_filepath = '/Users/stevenzhai/Desktop/MILP_data/sample-data-easy/1/1_7/optimus-code.py'
    transform_file_with_ast(input_filepath, output_filepath)
