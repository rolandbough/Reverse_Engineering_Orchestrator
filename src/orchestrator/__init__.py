"""
Reverse Engineering Workflow Orchestrator

ADR Note: Coordinates the end-to-end workflow:
Visual Analyzer → Memory Scanner → RE Tool → AI Analysis

This is the central coordinator that connects all components together.
"""

from .workflow_orchestrator import WorkflowOrchestrator

__all__ = ["WorkflowOrchestrator"]

