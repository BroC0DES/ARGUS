import ast
import os
import networkx as nx


CODEBASE_PATH = "mock_codebase"


def get_service_name(file_path):
    """
    Extract the service name from the file path.

    Example:
    mock_codebase/payment_service/payment.py

    becomes:
    payment_service
    """

    parts = file_path.split(os.sep)

    # Find the folder directly inside mock_codebase
    for i, part in enumerate(parts):
        if part == "mock_codebase" and i + 1 < len(parts):
            return parts[i + 1]

    return None


def analyze_file(file_path):
    """
    Read a Python file and return its imports.
    """

    with open(file_path, "r", encoding="utf-8") as file:
        source_code = file.read()

    tree = ast.parse(source_code)

    imports = []

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    return imports


def build_graph():

    graph = nx.DiGraph()

    for root, directories, files in os.walk(CODEBASE_PATH):

        for file in files:

            if not file.endswith(".py") or file == "__init__.py":
                continue

            file_path = os.path.join(root, file)

            source_service = get_service_name(file_path)

            if source_service is None:
                continue

            graph.add_node(source_service)

            imports = analyze_file(file_path)

            for imported_module in imports:

                parts = imported_module.split(".")

                if len(parts) >= 2:

                    target_service = parts[1]

                    if target_service != source_service:
                        graph.add_node(target_service)
                        graph.add_edge(source_service, target_service)

    return graph

if __name__ == "__main__":

    graph = build_graph()

    print("\nDependency Graph:")
    print("-----------------")

    for source, target in graph.edges():
        print(f"{source} -> {target}")

    # Convert graph into JSON format
    graph_data = {
        "nodes": [
            {"id": node}
            for node in graph.nodes()
        ],
        "edges": [
            {
                "source": source,
                "target": target
            }
            for source, target in graph.edges()
        ]
    }

    # Save graph as JSON
    os.makedirs("data", exist_ok=True)

    with open("data/dependency_graph.json", "w") as file:
        import json
        json.dump(graph_data, file, indent=4)

    print("\n✓ dependency_graph.json created")