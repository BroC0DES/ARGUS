import ast
import os
import json


CODEBASE_PATH = "mock_codebase"
OUTPUT_FILE = "data/code_index.json"


def analyze_file(file_path):
    print(f"\nScanning: {file_path}")

    with open(file_path, "r", encoding="utf-8") as file:
        source_code = file.read()

    tree = ast.parse(source_code)

    functions = []
    imports = []

    for node in ast.walk(tree):

        # Find functions and save their actual source code
        if isinstance(node, ast.FunctionDef):

            function_code = ast.get_source_segment(
                source_code,
                node
            )

            functions.append({
                "name": node.name,
                "code": function_code
            })

        # Find normal imports
        elif isinstance(node, ast.Import):

            for alias in node.names:
                imports.append(alias.name)

        # Find from ... import ...
        elif isinstance(node, ast.ImportFrom):

            if node.module:
                imports.append(node.module)

    print(
        "  Functions:",
        [function["name"] for function in functions]
    )

    print("  Imports:", imports)

    return {
        "file": file_path,
        "functions": functions,
        "imports": imports
    }


def scan_codebase():

    code_index = []

    for root, directories, files in os.walk(CODEBASE_PATH):

        for file in files:

            if file.endswith(".py") and file != "__init__.py":

                file_path = os.path.join(root, file)

                result = analyze_file(file_path)

                code_index.append(result)

    return code_index


if __name__ == "__main__":

    code_index = scan_codebase()

    os.makedirs("data", exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:

        json.dump(code_index, file, indent=4)

    print(f"\n✓ Code index saved to {OUTPUT_FILE}")