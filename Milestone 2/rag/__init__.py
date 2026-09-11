"""SupportPilot RAG package — Knowledge Retrieval & Resolution Generation."""
from .pipeline import run_rag_pipeline, get_rag_metrics
from .knowledge_base import KNOWLEDGE_BASE

__all__ = ["run_rag_pipeline", "get_rag_metrics", "KNOWLEDGE_BASE"]
