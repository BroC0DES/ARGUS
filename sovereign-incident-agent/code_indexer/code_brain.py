import json
import networkx as nx
import chromadb
import os


ANOMALY_FILE = "data/anomalies.json"
GRAPH_FILE = "data/dependency_graph.json"
CHROMA_PATH = "data/chroma_db"
OUTPUT_FILE = "data/incident_analysis.json"


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
# FIND CRITICAL INCIDENT
# --------------------------------------------------

def get_critical_anomaly(anomalies):

    for anomaly in anomalies:

        if anomaly["severity"] == "CRITICAL":
            return anomaly

    return None


# --------------------------------------------------
# FIND AFFECTED SERVICES
# --------------------------------------------------

def get_affected_services(graph, failed_service):

    return list(
        nx.ancestors(
            graph,
            failed_service
        )
    )


# --------------------------------------------------
# FIND IMPACT PATHS
# --------------------------------------------------

def get_impact_paths(graph, failed_service):

    paths = []

    affected_services = nx.ancestors(
        graph,
        failed_service
    )

    for service in affected_services:

        try:

            path = nx.shortest_path(
                graph,
                service,
                failed_service
            )

            paths.append(path)

        except nx.NetworkXNoPath:

            pass

    return paths


# --------------------------------------------------
# BUILD CODE SEARCH QUERY
# --------------------------------------------------

def build_query(anomaly):

    evidence = []

    for event in anomaly["evidence"]:

        message = event.get("message")

        if message:
            evidence.append(message)

    query = (
        f"{anomaly['service']} "
        f"{anomaly['type']} "
        f"{anomaly['severity']} "
        f"{anomaly['count']} occurrences "
        f"{' '.join(evidence[:10])}"
    )

    return query


# --------------------------------------------------
# SEARCH CODE USING CHROMADB
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

    for i in range(
        len(results["ids"][0])
    ):

        code_results.append({

            "function":
                results["metadatas"][0][i]["function"],

            "file":
                results["metadatas"][0][i]["file"]

        })

    return code_results


# --------------------------------------------------
# BUILD ROOT CAUSE CHAIN
# --------------------------------------------------

def build_root_cause_chain(
    anomaly,
    impact_paths
):

    service = anomaly["service"]
    anomaly_type = anomaly["type"]

    chain = []

    # Root event
    if anomaly_type == "TIMEOUT_CLUSTER":

        chain.append(
            f"{service}: Database connection timeouts"
        )

    elif anomaly_type == "CONNECTION_FAILURE":

        chain.append(
            f"{service}: Database connection failure"
        )

    elif anomaly_type == "REPEATED_500":

        chain.append(
            f"{service}: Repeated HTTP 500 errors"
        )

    else:

        chain.append(
            f"{service}: {anomaly_type}"
        )

    # Find services directly depending on root service
    direct_dependents = []

    for path in impact_paths:

        if len(path) >= 2:

            direct_service = path[-2]

            if direct_service not in direct_dependents:

                direct_dependents.append(
                    direct_service
                )

    if direct_dependents:

        chain.append(
            "Downstream operations affected: "
            + ", ".join(direct_dependents)
        )

    # Higher-level impact
    impacted_levels = []

    for path in impact_paths:

        for service_name in path[:-1]:

            if service_name not in impacted_levels:

                impacted_levels.append(
                    service_name
                )

    if impacted_levels:

        chain.append(
            "Failure propagated through: "
            + ", ".join(impacted_levels)
        )

    return chain


# --------------------------------------------------
# BUILD EVIDENCE → CONCLUSION
# --------------------------------------------------

def build_evidence_reasoning(
    anomaly,
    all_anomalies,
    affected_services
):

    observations = []

    # Root anomaly
    observations.append(
        f"{anomaly['count']} "
        f"{anomaly['type'].lower().replace('_', ' ')} "
        f"events detected in {anomaly['service']}"
    )

    # Other detected anomalies
    anomaly_types = []

    for detected in all_anomalies:

        if detected is anomaly:
            continue

        description = (
            f"{detected['type'].lower().replace('_', ' ')} "
            f"in {detected['service']}"
        )

        anomaly_types.append(description)

    if anomaly_types:

        observations.append(
            "Additional anomalies detected: "
            + "; ".join(anomaly_types)
        )

    # Downstream impact
    if affected_services:

        observations.append(
            "Dependent services were affected: "
            + ", ".join(affected_services)
        )

    # Root cause conclusion
    conclusion = (
        f"{anomaly['service']} is the probable root incident "
        f"because the {anomaly['type'].lower().replace('_', ' ')} "
        f"occurred at the dependency root and "
        f"downstream services subsequently showed failures."
    )

    return {
        "observations": observations,
        "conclusion": conclusion
    }


# --------------------------------------------------
# BUILD INCIDENT ANALYSIS
# --------------------------------------------------

def analyze_incident():

    anomalies = load_anomalies()

    graph = load_graph()

    anomaly = get_critical_anomaly(
        anomalies
    )

    if anomaly is None:

        return {
            "status":
                "NO_CRITICAL_INCIDENT"
        }

    failed_service = anomaly["service"]

    affected_services = get_affected_services(
        graph,
        failed_service
    )

    impact_paths = get_impact_paths(
        graph,
        failed_service
    )

    query = build_query(
        anomaly
    )

    relevant_code = search_code(
        query
    )

    evidence = []

    for event in anomaly["evidence"]:

        evidence.append({

            "timestamp":
                event["timestamp"],

            "service":
                event["service"],

            "severity":
                event["severity"],

            "message":
                event["message"]

        })

    root_cause_chain = build_root_cause_chain(
        anomaly,
        impact_paths
    )

    evidence_reasoning = build_evidence_reasoning(
    anomaly,
    anomalies,
    affected_services
)
    

    result = {

        "status":
            "INCIDENT_DETECTED",

        "root_incident": {

            "service":
                failed_service,

            "type":
                anomaly["type"],

            "severity":
                anomaly["severity"],

            "count":
                anomaly["count"]

        },

        "root_cause_chain":
            root_cause_chain,

        "evidence_reasoning":
            evidence_reasoning,

        "evidence":
            evidence,

        "affected_services":
            affected_services,

        "impact_paths":
            impact_paths,

        "relevant_code":
            relevant_code

    }

    return result


# --------------------------------------------------
# SAVE JSON RESULT
# --------------------------------------------------

def save_result(result):

    os.makedirs(
        "data",
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            result,
            file,
            indent=4
        )

    print(
        f"\n✓ Incident analysis saved to {OUTPUT_FILE}"
    )


# --------------------------------------------------
# PRINT HUMAN-READABLE REPORT
# --------------------------------------------------

def print_report(result):

    print("\n")
    print("=" * 60)
    print("              SOVEREIGN INCIDENT ANALYSIS")
    print("=" * 60)

    if result["status"] == "NO_CRITICAL_INCIDENT":

        print("\nNo critical incident detected.")

        return

    incident = result["root_incident"]

    print("\nROOT INCIDENT")
    print("-------------")

    print(
        f"Service  : {incident['service']}"
    )

    print(
        f"Type     : {incident['type']}"
    )

    print(
        f"Severity : {incident['severity']}"
    )

    print(
        f"Evidence : {incident['count']} events"
    )

    print("\nROOT CAUSE CHAIN")
    print("----------------")

    for i, step in enumerate(
        result["root_cause_chain"]
    ):

        print(step)

        if i < len(
            result["root_cause_chain"]
        ) - 1:

            print("       ↓")

    print("\nAFFECTED SERVICES")
    print("------------------")

    for service in result[
        "affected_services"
    ]:

        print(
            f"- {service}"
        )

    print("\nIMPACT PATHS")
    print("------------")

    for path in result[
        "impact_paths"
    ]:

        print(
            " -> ".join(path)
        )

    print("\nRELEVANT CODE")
    print("-------------")

    for code in result[
        "relevant_code"
    ]:

        print(
            f"- {code['function']} "
            f"({code['file']})"
        )

    print("\nEVIDENCE → CONCLUSION")
    print("---------------------")

    for observation in result[
        "evidence_reasoning"
    ]["observations"]:

        print(
            f"✓ {observation}"
        )

    print("\nConclusion:")

    print(
        result[
            "evidence_reasoning"
        ]["conclusion"]
    )

    print("\nEVIDENCE")
    print("--------")

    for event in result[
        "evidence"
    ][:10]:

        print(
            f"{event['timestamp']} | "
            f"{event['service']} | "
            f"{event['message']}"
        )

    print("\n")
    print("=" * 60)


# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":

    result = analyze_incident()

    save_result(result)

    print_report(result)