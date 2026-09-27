import json


GRAPH_FILE = "data/dependency_graph.json"
ANOMALY_FILE = "data/anomalies.json"
OUTPUT_FILE = "data/incident_context.json"


def load_json(file_path):

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def build_context():

    graph_data = load_json(GRAPH_FILE)
    anomaly_data = load_json(ANOMALY_FILE)

    context = {
        "dependency_graph": graph_data,
        "anomalies": anomaly_data["anomalies"]
    }

    return context


def save_context(context):

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:

        json.dump(context, file, indent=4)

    print(f"✓ Incident context saved to {OUTPUT_FILE}")


if __name__ == "__main__":

    context = build_context()

    print("\nIncident Context")
    print("----------------")

    print(
        f"Services: {len(context['dependency_graph']['nodes'])}"
    )

    print(
        f"Dependencies: {len(context['dependency_graph']['edges'])}"
    )

    print(
        f"Anomalies: {len(context['anomalies'])}"
    )

    save_context(context)