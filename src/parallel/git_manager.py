from typing import List, Optional, Dict
import git
from pathlib import Path
import asyncio
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class ParallelTask(BaseModel):
    """Represents a task that can be executed in parallel"""
    task_id: str
    branch_name: str
    dependencies: List[str] = []
    status: str = "pending"
    result: Optional[Dict] = None

class GitParallelManager:
    """Manages parallel execution using git branches"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.repo = git.Repo(repo_path)
        self.tasks: Dict[str, ParallelTask] = {}
        
    def create_parallel_task(self, task_id: str, dependencies: List[str] = None) -> ParallelTask:
        """Creates a new branch for parallel execution"""
        if dependencies is None:
            dependencies = []
            
        branch_name = f"parallel/{task_id}"
        
        # Create and checkout new branch
        current = self.repo.active_branch
        new_branch = self.repo.create_head(branch_name, current)
        new_branch.checkout()
        
        task = ParallelTask(
            task_id=task_id,
            branch_name=branch_name,
            dependencies=dependencies
        )
        self.tasks[task_id] = task
        
        return task
    
    async def execute_parallel(self, tasks: List[ParallelTask]):
        """Execute tasks in parallel, respecting dependencies"""
        dependency_graph = {task.task_id: task.dependencies for task in tasks}
        execution_order = self._topological_sort(dependency_graph)
        
        for layer in execution_order:
            # Tasks in the same layer can be executed in parallel
            await asyncio.gather(*[self._execute_task(task_id) for task_id in layer])
    
    async def _execute_task(self, task_id: str):
        """Execute a single task in its branch"""
        task = self.tasks[task_id]
        task.status = "running"
        
        try:
            # Checkout task branch
            self.repo.git.checkout(task.branch_name)
            
            # Here we would execute the actual task logic
            # For now, just a placeholder
            await asyncio.sleep(1)
            
            task.status = "completed"
            
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {str(e)}")
            task.status = "failed"
            task.result = {"error": str(e)}
    
    def _topological_sort(self, graph: Dict[str, List[str]]) -> List[List[str]]:
        """Sort tasks into layers that can be executed in parallel"""
        # Implementation of Kahn's algorithm
        in_degree = {node: 0 for node in graph}
        for node in graph:
            for neighbor in graph[node]:
                in_degree[neighbor] = in_degree.get(neighbor, 0) + 1
        
        # Queue of nodes with no incoming edges
        queue = [node for node, degree in in_degree.items() if degree == 0]
        layers = []
        
        while queue:
            current_layer = []
            next_queue = []
            
            for node in queue:
                current_layer.append(node)
                for neighbor in graph[node]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        next_queue.append(neighbor)
            
            layers.append(current_layer)
            queue = next_queue
        
        return layers

