"""Pre-defined workflow templates for OAgent."""

from oagent.graph.workflows.basic_react import create_react_workflow
from oagent.graph.workflows.rag_workflow import create_rag_workflow
from oagent.graph.workflows.human_in_loop import create_human_in_loop_workflow

__all__ = [
    "create_react_workflow",
    "create_rag_workflow",
    "create_human_in_loop_workflow",
]
