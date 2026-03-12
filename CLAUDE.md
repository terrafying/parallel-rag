# CLAUDE.md — Parallel RAG Codebase Guide

This file provides guidance for AI assistants working in this repository.

## Project Overview

**Parallel RAG** is a distributed Retrieval Augmented Generation (RAG) system that uses git branches as a runtime parallel execution mechanism. The core architectural novelty is that git branches represent parallel task execution units rather than just version control branches.

- **Version**: 0.1.0 (early development)
- **Python**: >=3.8
- **Status**: Initial structure in place; most modules are stubs awaiting implementation

## Repository Structure

```
parallel-rag/
├── pyproject.toml          # Project metadata and dependencies
├── README.md               # High-level overview
├── CLAUDE.md               # This file
└── src/
    ├── __init__.py
    ├── core/               # Core RAG logic (implemented)
    │   ├── config.py       # Pydantic config models
    │   └── engine.py       # RAGEngine, Query, Response classes
    ├── parallel/           # Git-based parallel execution (implemented)
    │   └── git_manager.py  # GitParallelManager, ParallelTask
    ├── api/                # FastAPI layer (stub — empty)
    ├── orchestration/      # Orchestration layer (stub — empty)
    ├── topology/           # Topology management (stub — empty)
    └── viz/                # Visualization (stub — empty)
```

Packages are discovered from the `src/` directory via `[tool.setuptools.packages.find]`.

## Key Concepts

### Git-Based Parallelism

The central design pattern: `GitParallelManager` creates a git branch per task (`parallel/<task_id>`), checks it out, and executes the task there. Tasks are grouped into dependency layers using Kahn's topological sort algorithm, and each layer is executed concurrently with `asyncio.gather()`.

This means **the working git repo's branches are mutated at runtime**. Do not be surprised to find `parallel/*` branches in the repo after execution.

### Task Execution Flow

1. `RAGEngine.process_query()` creates three tasks: `retrieval` → `reasoning` → `generation` (sequential chain via dependencies)
2. `RAGEngine.update_knowledge()` creates one `process_doc_<i>` task per document (all parallel), then a single `indexing` task dependent on all of them
3. `GitParallelManager.execute_parallel()` resolves dependency layers and runs each layer with `asyncio.gather()`

### Configuration

All config is done via Pydantic models in `src/core/config.py`. The mandatory field is `parallel.git_repo_path` (a `Path`). All other fields have sensible defaults:

| Config Class | Key Fields | Defaults |
|---|---|---|
| `VectorStoreConfig` | `engine`, `dimension`, `metric` | `faiss`, `768`, `cosine` |
| `Z3SolverConfig` | `timeout`, `proof_mode` | `5000ms`, `False` |
| `ParallelConfig` | `max_parallel_tasks`, `task_timeout`, `branch_prefix` | `10`, `3600s`, `"parallel"` |
| `RAGConfig` | `model_name`, `chunk_size`, `temperature` | `gpt-3.5-turbo`, `512`, `0.7` |

There is no `.env` file. Configuration is passed programmatically by instantiating `RAGConfig`.

## Tech Stack

| Dependency | Role |
|---|---|
| `exo-explore` | Topology, orchestration, and visualization framework (planned integration) |
| `gitpython` | Git operations for parallel task branch management |
| `z3-solver` | SMT solver for constrained reasoning |
| `pydantic` | Data validation and settings models |
| `fastapi` | HTTP API layer (not yet implemented) |
| `torch` + `numpy` | ML inference and numerical computing |

## Development Setup

```bash
# Install in editable mode
pip install -e .
```

There is no Makefile, no pre-commit hooks, and no CI/CD configuration at this time.

## Testing

No tests exist yet. The `pyproject.toml` excludes `tests*` from package builds, anticipating a future `tests/` directory.

When adding tests, use `pytest`. Place them in a top-level `tests/` directory (not under `src/`).

## Coding Conventions

- **Async-first**: All task execution is `async`. New engine or manager methods should be `async def` where I/O or parallelism is involved.
- **Pydantic models for data**: `Query`, `Response`, `ParallelTask` are all `BaseModel` subclasses. Follow this pattern for any new data structures.
- **Type hints required**: All function signatures must have full type annotations.
- **Logging**: Use `logging.getLogger(__name__)` per module. Do not use `print()`.
- **Error handling**: Catch exceptions in `_execute_task`, log with `logger.error()`, set `task.status = "failed"`, and store error in `task.result`.

## Module Completion Status

| Module | Status | Notes |
|---|---|---|
| `src/core/config.py` | Done | All config classes implemented |
| `src/core/engine.py` | Partial | Placeholder response; actual retrieval/reasoning/generation not wired in |
| `src/parallel/git_manager.py` | Partial | Branch creation + topological scheduling done; task logic is a `sleep(1)` stub |
| `src/api/` | Stub | Empty `__init__.py` only |
| `src/orchestration/` | Stub | Empty `__init__.py` only |
| `src/topology/` | Stub | Empty `__init__.py` only |
| `src/viz/` | Stub | Empty `__init__.py` only |

## Important Caveats for AI Assistants

1. **Branch mutations**: `GitParallelManager.create_parallel_task()` immediately creates and checks out a git branch. Implementing or testing this code will modify the active branch of whatever repo path is provided. Always use a dedicated test repo path, never the development repo itself.

2. **Topological sort direction**: The `_topological_sort` in `git_manager.py` builds `in_degree` by iterating `graph[node]` as *neighbors of node* — meaning `dependencies` lists are treated as nodes that the current node *points to*, not nodes that *depend on* the current node. Verify this matches intent before extending task scheduling logic.

3. **No vector store wired up**: Despite `VectorStoreConfig` supporting FAISS/Milvus/Qdrant, no actual vector store is instantiated anywhere yet. The retrieval task is a stub.

4. **model_name defaults to GPT**: `RAGConfig.model_name = "gpt-3.5-turbo"` but the project uses no OpenAI SDK. This will need updating when the LLM integration is implemented.

## Git Branch Conventions

- Development branches: `claude/<description>-<session-id>` or `feature/<description>`
- Runtime parallel task branches (auto-created): `parallel/<task_id>`
- Main branch: `master` (local) / `main` (remote origin)

Do not push `parallel/*` branches to remote; they are ephemeral runtime artifacts.
