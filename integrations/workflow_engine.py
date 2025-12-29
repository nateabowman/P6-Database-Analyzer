"""Workflow automation engine."""

from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from utils.logging_config import get_logger

logger = get_logger(__name__)


class WorkflowStep:
    """Represents a workflow step."""
    
    def __init__(
        self,
        name: str,
        action: Callable,
        condition: Optional[Callable] = None,
        on_success: Optional[str] = None,
        on_failure: Optional[str] = None
    ):
        self.name = name
        self.action = action
        self.condition = condition
        self.on_success = on_success
        self.on_failure = on_failure


class WorkflowEngine:
    """Executes automated workflows."""
    
    def __init__(self):
        self.workflows: Dict[str, List[WorkflowStep]] = {}
    
    def register_workflow(self, name: str, steps: List[WorkflowStep]):
        """Register a workflow."""
        self.workflows[name] = steps
        logger.info(f"Workflow registered: {name} with {len(steps)} steps")
    
    async def execute_workflow(self, name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow."""
        if name not in self.workflows:
            raise ValueError(f"Workflow '{name}' not found")
        
        logger.info(f"Executing workflow: {name}")
        results = []
        
        for step in self.workflows[name]:
            # Check condition
            if step.condition and not step.condition(context):
                logger.debug(f"Skipping step {step.name} due to condition")
                continue
            
            try:
                result = await step.action(context)
                results.append({'step': step.name, 'status': 'success', 'result': result})
                context.update(result or {})
            except Exception as e:
                logger.error(f"Workflow step {step.name} failed: {str(e)}")
                results.append({'step': step.name, 'status': 'failure', 'error': str(e)})
                if step.on_failure:
                    # Handle failure
                    pass
                break
        
        return {'workflow': name, 'results': results}

