import chromadb


CHROMA_PATH = "data/chroma_db"


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

    print("\nIncident Query:")
    print(query)

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

    query = input(
        "\nEnter incident description: "
    )

    search_code(query)