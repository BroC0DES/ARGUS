import json
import chromadb


INDEX_FILE = "data/code_index.json"
CHROMA_PATH = "data/chroma_db"


def load_code_index():

    with open(INDEX_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def create_documents(code_index):

    documents = []
    ids = []
    metadata = []

    for file_data in code_index:

        file_path = file_data["file"]

        for function in file_data["functions"]:

            function_name = function["name"]
            function_code = function["code"]

            documents.append(function_code)

            ids.append(
                f"{file_path}:{function_name}"
            )

            metadata.append({
                "file": file_path,
                "function": function_name
            })

    return documents, ids, metadata


def main():

    print("Loading code index...")

    code_index = load_code_index()

    documents, ids, metadata = create_documents(code_index)

    print(f"Functions found: {len(documents)}")

    client = chromadb.PersistentClient(
        path=CHROMA_PATH
    )

    collection = client.get_or_create_collection(
        name="codebase"
    )

    collection.upsert(
        documents=documents,
        ids=ids,
        metadatas=metadata
    )

    print("\n✓ Code successfully indexed into ChromaDB")

    print(f"Stored functions: {collection.count()}")


if __name__ == "__main__":
    main()