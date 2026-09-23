"""
Knowledge-base retrieval using TF-IDF + cosine similarity.
This is the "R" in RAG.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class KnowledgeRetriever:
    def __init__(self, documents):
        self.documents = documents
        self.texts = [
            f"{doc['title']} {doc['content']}" for doc in documents
        ]
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.document_vectors = self.vectorizer.fit_transform(self.texts)

    def search(self, query: str, top_k: int = 3, min_score: float = 0.05):
        """
        Return the top_k most relevant documents for the query.
        Filters out results below min_score.
        """
        if not query or not query.strip():
            return []

        query_vector = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self.document_vectors)[0]
        ranked_indices = scores.argsort()[::-1]

        results = []
        for index in ranked_indices[:top_k]:
            score = float(scores[index])
            if score < min_score:
                continue
            doc = self.documents[index]
            results.append(
                {
                    "id": doc["id"],
                    "title": doc["title"],
                    "category": doc["category"],
                    "content": doc["content"],
                    "score": score,
                }
            )
        return results
