import json
import chromadb


ANOMALY_FILE = "data/anomalies.json"
CHROMA_PATH = "data/chroma_db"


def load_anomalies():

    with open(
        ANOMALY_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)["anomalies"]


def build_query(anomaly):

    service = anomaly["service"]
    anomaly_type = anomaly["type"]
    severity = anomaly["severity"]
    count = anomaly["count"]

    evidence_messages = []

    for event in anomaly["evidence"]:

        message = event.get("message")

        if message:
            evidence_messages.append(message)

    evidence_text = " ".join(
        evidence_messages[:10]
    )

    query = (
        f"{service} {anomaly_type} "
        f"{severity} failure "
        f"{count} occurrences "
        f"{evidence_text}"
    )

    return query
    


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

    return results


def main():

    anomalies = load_anomalies()

    print("\nDetected Anomalies:")
    print("-------------------")

    for i, anomaly in enumerate(anomalies):

        print(
            f"{i + 1}. "
            f"{anomaly['service']} | "
            f"{anomaly['type']} | "
            f"{anomaly['severity']}"
        )

    # Use the first critical anomaly
    critical_anomaly = next(
        anomaly
        for anomaly in anomalies
        if anomaly["severity"] == "CRITICAL"
    )

    query = build_query(critical_anomaly)

    print("\nIncident Query:")
    print(query)

    results = search_code(query)

    print("\nRelevant Code:")
    print("----------------")

    for i in range(len(results["ids"][0])):

        print(f"\nResult {i + 1}")

        print(
            "Function:",
            results["metadatas"][0][i]["function"]
        )

        print(
            "File:",
            results["metadatas"][0][i]["file"]
        )

        print("Code:")

        print(
            results["documents"][0][i]
        )


if __name__ == "__main__":
    main()