import json
import networkx as nx


GRAPH_FILE = "data/dependency_graph.json"


def load_graph():

    with open(
        GRAPH_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    graph = nx.DiGraph()

    # Add nodes
    for node in data["nodes"]:
        graph.add_node(node["id"])

    # Add edges
    for edge in data["edges"]:
        graph.add_edge(
            edge["source"],
            edge["target"]
        )

    return graph


def find_affected_services(graph, failed_service):

    return nx.ancestors(
        graph,
        failed_service
    )


def main():

    graph = load_graph()

    failed_service = "database_service"

    affected_services = find_affected_services(
        graph,
        failed_service
    )

    print("\nFailed Service:")
    print("----------------")
    print(failed_service)

    print("\nAffected Services:")
    print("------------------")

    for service in affected_services:
        print(service)


if __name__ == "__main__":
    main()