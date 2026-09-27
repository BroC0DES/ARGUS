import json
import networkx as nx
import chromadb


ANOMALY_FILE = "data/anomalies.json"
GRAPH_FILE = "data/dependency_graph.json"
CHROMA_PATH = "data/chroma_db"


# --------------------------------------------------
# LOAD ANOMALIES
# --------------------------------------------------

def load_anomalies():

    with open(
        ANOMALY_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)["anomalies"]


# --------------------------------------------------
# LOAD DEPENDENCY GRAPH
# --------------------------------------------------

def load_graph():

    with open(
        GRAPH_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    graph = nx.DiGraph()

    for node in data["nodes"]:
        graph.add_node(node["id"])

    for edge in data["edges"]:
        graph.add_edge(
            edge["source"],
            edge["target"]
        )

    return graph


# --------------------------------------------------
# SEARCH CODE
# --------------------------------------------------

def search_code(query):

    client = chromadb.PersistentClient(
        path=CHROMA_PATH
    )

    collection = client.get_collection(
        name="codebase"
    )

    results = collection.query(
        query_texts=[query],
        n_results=5
    )

    code_results = []

    for i in range(len(results["ids"][0])):

        code_results.append({
            "function":
                results["metadatas"][0][i]["function"],

            "file":
                results["metadatas"][0][i]["file"],

            "code":
                results["documents"][0][i]
        })

    return code_results


# --------------------------------------------------
# MAIN ANALYSIS
# --------------------------------------------------

def main():

    anomalies = load_anomalies()

    graph = load_graph()

    # Select first critical anomaly

    critical_anomaly = next(
        anomaly
        for anomaly in anomalies
        if anomaly["severity"] == "CRITICAL"
    )

    failed_service = critical_anomaly["service"]

    # Find affected services

    affected_services = nx.ancestors(
        graph,
        failed_service
    )

    # Build code-search query

    evidence_messages = []

    for event in critical_anomaly["evidence"]:

        message = event.get("message")

        if message:
            evidence_messages.append(message)

    query = (
        f"{failed_service} "
        f"{critical_anomaly['type']} "
        f"{critical_anomaly['severity']} "
        f"{' '.join(evidence_messages[:10])}"
    )

    relevant_code = search_code(query)

    # --------------------------------------------------
    # PRINT FINAL REPORT
    # --------------------------------------------------

    print("\n")
    print("=" * 55)
    print("              INCIDENT ANALYSIS")
    print("=" * 55)

    print("\nRoot Incident:")
    print(
        f"{failed_service} "
        f"{critical_anomaly['type']}"
    )

    print("\nSeverity:")
    print(
        critical_anomaly["severity"]
    )

    print("\nEvidence:")
    print(
        f"{critical_anomaly['count']} "
        f"events detected"
    )

    print("\nAffected Services:")

    for service in affected_services:
        print(f"- {service}")

    print("\nRelevant Code:")

    for item in relevant_code:

        print(
            f"- {item['function']} "
            f"({item['file']})"
        )

    print("\nDependency Impact:")

    print(
        "database_service"
    )

    print("    ↑")

    print(
        "inventory_service / payment_service"
    )

    print("    ↑")

    print(
        "order_service"
    )

    print("    ↑")

    print(
        "api_gateway"
    )

    print("\n")
    print("=" * 55)


if __name__ == "__main__":
    main()