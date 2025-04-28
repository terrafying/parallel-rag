from pydantic import BaseModel
from typing import Optional, Dict, List
from pathlib import Path

class VectorStoreConfig(BaseModel):
    """Configuration for vector storage"""
    engine: str = "faiss"  # or "milvus", "qdrant", etc.
    dimension: int = 768
    metric: str = "cosine"
    index_params: Optional[Dict] = None

class Z3SolverConfig(BaseModel):
    """Configuration for Z3 solver integration"""
    timeout: int = 5000  # milliseconds
    max_conflicts: Optional[int] = None
    proof_mode: bool = False

class ParallelConfig(BaseModel):
    """Configuration for parallel execution"""
    max_parallel_tasks: int = 10
    task_timeout: int = 3600  # seconds
    git_repo_path: Path
    branch_prefix: str = "parallel"

class RAGConfig(BaseModel):
    """Main configuration for the RAG system"""
    vector_store: VectorStoreConfig = VectorStoreConfig()
    z3_solver: Z3SolverConfig = Z3SolverConfig()
    parallel: ParallelConfig
    model_name: str = "gpt-3.5-turbo"
    chunk_size: int = 512
    chunk_overlap: int = 50
    temperature: float = 0.7
    max_tokens: int = 2000

