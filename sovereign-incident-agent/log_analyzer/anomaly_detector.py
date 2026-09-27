import re
import json
import os
from datetime import datetime


LOG_FILE = "logs/system.log"
OUTPUT_FILE = "data/anomalies.json"


# --------------------------------------------------
# 1. PARSE LOG LINE
# --------------------------------------------------

def parse_log_line(line):

    pattern = r"(\d{2}:\d{2}:\d{2})\s+(INFO|ERROR|WARNING)\s+(\w+)\s+(.+)"

    match = re.match(pattern, line)

    if not match:
        return None

    timestamp = match.group(1)

    return {
        "timestamp": timestamp,
        "severity": match.group(2),
        "service": match.group(3),
        "message": match.group(4)
    }


# --------------------------------------------------
# 2. CLASSIFY ERROR
# --------------------------------------------------

def detect_error_type(message):

    message = message.lower()

    if "connection timeout" in message:
        return "TIMEOUT"

    if "connection refused" in message:
        return "CONNECTION_REFUSED"

    if "database unavailable" in message:
        return "DATABASE_UNAVAILABLE"

    if "http 500" in message:
        return "HTTP_500"

    if "payment failed" in message:
        return "PAYMENT_FAILURE"

    if "inventory check failed" in message:
        return "INVENTORY_FAILURE"

    return "UNKNOWN_ERROR"


# --------------------------------------------------
# 3. CONVERT TIME TO SECONDS
# --------------------------------------------------

def time_to_seconds(timestamp):

    time = datetime.strptime(
        timestamp,
        "%H:%M:%S"
    )

    return (
        time.hour * 3600
        + time.minute * 60
        + time.second
    )


# --------------------------------------------------
# 4. READ LOG FILE
# --------------------------------------------------

def read_logs():

    events = []

    with open(LOG_FILE, "r", encoding="utf-8") as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            event = parse_log_line(line)

            if event:

                event["time_seconds"] = time_to_seconds(
                    event["timestamp"]
                )

                if event["severity"] == "ERROR":

                    event["error_type"] = detect_error_type(
                        event["message"]
                    )

                events.append(event)

    return events


# --------------------------------------------------
# 5. DETECT TIMEOUT CLUSTERS
# --------------------------------------------------

def detect_timeout_clusters(events):

    timeout_events = [
        event
        for event in events
        if event.get("error_type") == "TIMEOUT"
    ]

    anomalies = []

    for i in range(len(timeout_events)):

        cluster = []

        start_time = timeout_events[i]["time_seconds"]

        for event in timeout_events[i:]:

            if event["time_seconds"] - start_time <= 60:

                cluster.append(event)

            else:
                break

        if len(cluster) >= 3:

            anomalies.append({
                "service": "database_service",
                "type": "TIMEOUT_CLUSTER",
                "severity": "CRITICAL",
                "count": len(cluster),
                "evidence": cluster
            })

            break

    return anomalies


# --------------------------------------------------
# 6. DETECT CONNECTION FAILURES
# --------------------------------------------------

def detect_connection_failures(events):

    connection_errors = [
        event
        for event in events
        if event.get("error_type") in [
            "CONNECTION_REFUSED",
            "DATABASE_UNAVAILABLE"
        ]
    ]

    if not connection_errors:
        return []

    return [{
        "service": "database_service",
        "type": "CONNECTION_FAILURE",
        "severity": "CRITICAL",
        "count": len(connection_errors),
        "evidence": connection_errors
    }]


# --------------------------------------------------
# 7. DETECT HTTP 500 SPIKE
# --------------------------------------------------

def detect_http_500(events):

    http_500_events = [
        event
        for event in events
        if event.get("error_type") == "HTTP_500"
    ]

    if len(http_500_events) >= 3:

        return [{
            "service": "api_gateway",
            "type": "REPEATED_500",
            "severity": "HIGH",
            "count": len(http_500_events),
            "evidence": http_500_events
        }]

    return []


# --------------------------------------------------
# 8. DETECT SERVICE ERROR SPIKES
# --------------------------------------------------

def detect_error_spikes(events):

    anomalies = []

    services = set(
        event["service"]
        for event in events
        if event["severity"] == "ERROR"
    )

    for service in services:

        service_errors = [
            event
            for event in events
            if event["service"] == service
            and event["severity"] == "ERROR"
        ]

        for i in range(len(service_errors)):

            cluster = []

            start_time = service_errors[i]["time_seconds"]

            for event in service_errors[i:]:

                if event["time_seconds"] - start_time <= 60:

                    cluster.append(event)

                else:
                    break

            if len(cluster) >= 5:

                anomalies.append({
                    "service": service,
                    "type": "ERROR_SPIKE",
                    "severity": "HIGH",
                    "count": len(cluster),
                    "evidence": cluster
                })

                break

    return anomalies


# --------------------------------------------------
# 9. RUN ALL DETECTORS
# --------------------------------------------------

def detect_anomalies(events):

    anomalies = []

    anomalies.extend(
        detect_timeout_clusters(events)
    )

    anomalies.extend(
        detect_connection_failures(events)
    )

    anomalies.extend(
        detect_http_500(events)
    )

    anomalies.extend(
        detect_error_spikes(events)
    )

    return anomalies


# --------------------------------------------------
# 10. SAVE RESULTS
# --------------------------------------------------

def save_results(anomalies):

    os.makedirs("data", exist_ok=True)

    result = {
        "anomalies": anomalies
    }

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

    print("\nAnomaly Detection Results:")
    print("--------------------------")

    for anomaly in anomalies:

        print(
            f"{anomaly['service']} | "
            f"{anomaly['type']} | "
            f"{anomaly['severity']} | "
            f"count={anomaly['count']}"
        )

    print(
        f"\n✓ Results saved to {OUTPUT_FILE}"
    )


# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":

    events = read_logs()

    print(
        f"Total log events: {len(events)}"
    )

    anomalies = detect_anomalies(events)

    save_results(anomalies)