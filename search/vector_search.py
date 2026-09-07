"""Shared kNN query helper for the semantic retrieval experiments (EXP22/23/24/30) — the
mechanical part (embed the query, run a knn query against one vector field) is identical across
them; only which field differs."""

from embeddings import embed_query
from vector_mapping import INDEX_NAME


def make_vector_search_fn(client, field_name: str, k: int = 50):
    def search(query: str) -> list[str]:
        query_vector = embed_query(query)
        resp = client.search(
            index=INDEX_NAME,
            body={"query": {"knn": {field_name: {"vector": query_vector, "k": k}}}, "size": k},
        )
        return [hit["_source"]["product_id"] for hit in resp["hits"]["hits"]]

    return search
