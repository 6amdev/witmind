#!/usr/bin/env python3
"""
Monitoring & Logging - Production-ready observability

Features:
- Structured logging
- Performance metrics
- Cost tracking
- Error reporting
"""

import logging
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from contextlib import contextmanager


@dataclass
class AgentMetrics:
    """Metrics for an agent execution"""
    agent_id: str
    task_type: str
    started_at: str
    completed_at: Optional[str] = None
    duration_seconds: float = 0.0

    # LLM usage
    llm_calls: int = 0
    tokens_input: int = 0
    tokens_output: int = 0
    estimated_cost_usd: float = 0.0

    # Tools usage
    tool_calls: int = 0
    tool_calls_by_type: Dict[str, int] = None

    # Results
    success: bool = False
    iterations: int = 0
    deliverables: List[str] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.tool_calls_by_type is None:
            self.tool_calls_by_type = {}
        if self.deliverables is None:
            self.deliverables = []


class MetricsCollector:
    """Collect and aggregate metrics"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metrics: List[AgentMetrics] = []

    def record_agent_execution(self, metrics: AgentMetrics):
        """Record agent execution metrics"""
        self.metrics.append(metrics)

        # Save to file
        metrics_file = self.output_dir / f"metrics_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(metrics_file, 'a') as f:
            f.write(json.dumps(asdict(metrics)) + '\n')

    def get_summary(self) -> Dict:
        """Get summary of all metrics"""
        if not self.metrics:
            return {'total_executions': 0}

        total_cost = sum(m.estimated_cost_usd for m in self.metrics)
        total_duration = sum(m.duration_seconds for m in self.metrics)
        total_tokens = sum(m.tokens_input + m.tokens_output for m in self.metrics)

        success_count = sum(1 for m in self.metrics if m.success)

        return {
            'total_executions': len(self.metrics),
            'successful': success_count,
            'failed': len(self.metrics) - success_count,
            'total_cost_usd': round(total_cost, 4),
            'total_duration_seconds': round(total_duration, 2),
            'total_tokens': total_tokens,
            'avg_cost_per_execution': round(total_cost / len(self.metrics), 4),
            'avg_duration_seconds': round(total_duration / len(self.metrics), 2),
        }


class CostTracker:
    """Track LLM costs"""

    # Pricing per 1M tokens (as of 2026)
    PRICING = {
        'claude-sonnet-4': {'input': 3.0, 'output': 15.0},
        'claude-haiku-4': {'input': 0.25, 'output': 1.25},
        'openrouter-claude-sonnet': {'input': 3.0, 'output': 15.0},
        'openrouter-gemini-flash': {'input': 0.0, 'output': 0.0},  # Free!
        'ollama': {'input': 0.0, 'output': 0.0},  # Free
    }

    @staticmethod
    def calculate_cost(
        model: str,
        tokens_input: int,
        tokens_output: int
    ) -> float:
        """Calculate cost in USD"""
        pricing = CostTracker.PRICING.get(model, {'input': 3.0, 'output': 15.0})

        cost_input = (tokens_input / 1_000_000) * pricing['input']
        cost_output = (tokens_output / 1_000_000) * pricing['output']

        return cost_input + cost_output


@contextmanager
def track_execution(
    agent_id: str,
    task_type: str,
    collector: Optional[MetricsCollector] = None
):
    """
    Context manager to track agent execution.

    Usage:
        with track_execution('pm', 'analyze_requirements', collector) as tracker:
            # Do work
            tracker.record_llm_call(tokens_in=100, tokens_out=500)
            tracker.record_tool_call('read_file')
            tracker.set_success(True)
    """
    metrics = AgentMetrics(
        agent_id=agent_id,
        task_type=task_type,
        started_at=datetime.utcnow().isoformat()
    )

    start_time = time.time()

    class Tracker:
        def record_llm_call(self, tokens_in: int, tokens_out: int, model: str = 'claude-sonnet-4'):
            metrics.llm_calls += 1
            metrics.tokens_input += tokens_in
            metrics.tokens_output += tokens_out
            metrics.estimated_cost_usd += CostTracker.calculate_cost(model, tokens_in, tokens_out)

        def record_tool_call(self, tool_name: str):
            metrics.tool_calls += 1
            metrics.tool_calls_by_type[tool_name] = metrics.tool_calls_by_type.get(tool_name, 0) + 1

        def set_success(self, success: bool):
            metrics.success = success

        def set_error(self, error: str):
            metrics.error = error
            metrics.success = False

        def add_deliverable(self, file_path: str):
            metrics.deliverables.append(file_path)

        def set_iterations(self, count: int):
            metrics.iterations = count

    tracker = Tracker()

    try:
        yield tracker
    finally:
        metrics.completed_at = datetime.utcnow().isoformat()
        metrics.duration_seconds = time.time() - start_time

        if collector:
            collector.record_agent_execution(metrics)


class StructuredLogger:
    """Structured logging for better observability"""

    def __init__(self, name: str, log_file: Optional[Path] = None):
        self.logger = logging.getLogger(name)
        self.log_file = log_file

        # Configure handler
        if log_file:
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def log_agent_start(self, agent_id: str, task: Dict):
        """Log agent start"""
        self.logger.info(f"Agent {agent_id} started", extra={
            'agent_id': agent_id,
            'task_type': task.get('type'),
            'event': 'agent_start'
        })

    def log_agent_complete(self, agent_id: str, success: bool, duration: float):
        """Log agent completion"""
        level = logging.INFO if success else logging.ERROR
        self.logger.log(level, f"Agent {agent_id} completed", extra={
            'agent_id': agent_id,
            'success': success,
            'duration_seconds': duration,
            'event': 'agent_complete'
        })

    def log_tool_call(self, tool_name: str, success: bool):
        """Log tool call"""
        self.logger.debug(f"Tool {tool_name} called", extra={
            'tool_name': tool_name,
            'success': success,
            'event': 'tool_call'
        })

    def log_error(self, error: str, context: Dict = None):
        """Log error with context"""
        self.logger.error(error, extra={
            'event': 'error',
            'context': context or {}
        })


def setup_production_logging(log_dir: Path):
    """
    Setup production-grade logging.

    Creates:
    - app.log - Application logs
    - errors.log - Error-only logs
    - metrics/ - Metrics files
    """
    log_dir.mkdir(parents=True, exist_ok=True)

    # Main app logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'app.log'),
            logging.StreamHandler()
        ]
    )

    # Error logger
    error_handler = logging.FileHandler(log_dir / 'errors.log')
    error_handler.setLevel(logging.ERROR)
    logging.getLogger().addHandler(error_handler)

    # Create metrics dir
    (log_dir / 'metrics').mkdir(exist_ok=True)

    logging.info("Production logging configured")

    return log_dir


# Example usage
if __name__ == '__main__':
    # Setup
    metrics_dir = Path('~/witmind-data/metrics').expanduser()
    collector = MetricsCollector(metrics_dir)

    # Track execution
    with track_execution('pm', 'analyze_requirements', collector) as tracker:
        time.sleep(0.1)  # Simulate work
        tracker.record_llm_call(tokens_in=1000, tokens_out=500, model='claude-sonnet-4')
        tracker.record_tool_call('read_file')
        tracker.record_tool_call('write_file')
        tracker.add_deliverable('SPEC.md')
        tracker.set_success(True)

    # Get summary
    print("Metrics Summary:")
    print(json.dumps(collector.get_summary(), indent=2))
