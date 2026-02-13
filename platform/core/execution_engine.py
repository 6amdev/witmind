#!/usr/bin/env python3
"""
Execution Engine for WitMind.AI Platform
Handles task execution with retry logic, parallel execution, and flexible approval
"""

import os
import json
import time
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed


class ApprovalMode(Enum):
    """Approval modes for stages"""
    BLOCKING = "blocking"      # Wait for human approval
    ASYNC = "async"            # Continue, mark pending review
    AUTO = "auto"              # Auto-approve based on confidence
    POST_REVIEW = "post_review"  # Do work, review later


class TaskStatus(Enum):
    """Status of a task"""
    PENDING = "pending"
    RUNNING = "running"
    RETRYING = "retrying"
    SUCCESS = "success"
    FAILED = "failed"
    ESCALATED = "escalated"
    SKIPPED = "skipped"


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_retries: int = 3
    retry_delay: int = 5  # seconds
    retry_on: List[str] = field(default_factory=lambda: [
        "test_failure", "build_error", "lint_error"
    ])
    no_retry_on: List[str] = field(default_factory=lambda: [
        "security_vulnerability", "api_rate_limit"
    ])
    escalate_after: int = 3


@dataclass
class ConfidenceConfig:
    """Configuration for confidence-based auto approval"""
    threshold: float = 0.8
    weights: Dict[str, float] = field(default_factory=lambda: {
        "tests_passed": 0.3,
        "no_errors": 0.2,
        "follows_spec": 0.2,
        "code_quality": 0.15,
        "security_scan": 0.15
    })


@dataclass
class TaskResult:
    """Result of a task execution"""
    success: bool
    output: Any = None
    errors: List[str] = field(default_factory=list)
    test_results: Optional[Dict] = None
    confidence_score: float = 0.0
    attempt: int = 1
    duration: float = 0.0


@dataclass
class ExecutionContext:
    """Context for task execution"""
    project_id: str
    project_path: Path
    stage: str
    agent_id: str
    task: Dict
    retry_config: RetryConfig = field(default_factory=RetryConfig)
    confidence_config: ConfidenceConfig = field(default_factory=ConfidenceConfig)


class ConfidenceCalculator:
    """Calculate confidence score for auto-approval"""

    def __init__(self, config: ConfidenceConfig):
        self.config = config

    def calculate(self, result: TaskResult) -> float:
        """Calculate confidence score based on task result"""
        score = 0.0
        weights = self.config.weights

        # Tests passed
        if result.test_results:
            if result.test_results.get("all_passed", False):
                score += weights.get("tests_passed", 0.3)
            elif result.test_results.get("pass_rate", 0) > 0.9:
                score += weights.get("tests_passed", 0.3) * 0.7

        # No errors
        if len(result.errors) == 0:
            score += weights.get("no_errors", 0.2)

        # Code quality (if available)
        code_quality = result.test_results.get("code_quality", 0) if result.test_results else 0
        score += code_quality * weights.get("code_quality", 0.15)

        # Security scan
        security_issues = result.test_results.get("security_issues", 0) if result.test_results else 0
        if security_issues == 0:
            score += weights.get("security_scan", 0.15)

        # Follows spec (simplified - based on output existence)
        if result.output:
            score += weights.get("follows_spec", 0.2)

        return min(score, 1.0)

    def should_auto_approve(self, result: TaskResult) -> bool:
        """Check if result should be auto-approved"""
        score = self.calculate(result)
        result.confidence_score = score
        return score >= self.config.threshold


class RetryLoop:
    """Handles retry logic for agent tasks"""

    def __init__(self, config: RetryConfig):
        self.config = config
        self.attempt_history: List[Dict] = []

    def should_retry(self, error_type: str) -> bool:
        """Check if error type is retryable"""
        if error_type in self.config.no_retry_on:
            return False
        return error_type in self.config.retry_on or len(self.config.retry_on) == 0

    async def execute_with_retry(
        self,
        task_func: Callable,
        error_analyzer: Callable,
        fix_applier: Callable,
        context: ExecutionContext
    ) -> TaskResult:
        """Execute task with automatic retry on failure"""

        for attempt in range(1, self.config.max_retries + 1):
            start_time = time.time()

            try:
                # Execute task
                result = await task_func(context)
                result.attempt = attempt
                result.duration = time.time() - start_time

                # Record attempt
                self.attempt_history.append({
                    "attempt": attempt,
                    "success": result.success,
                    "errors": result.errors,
                    "duration": result.duration,
                    "timestamp": datetime.now().isoformat()
                })

                if result.success:
                    return result

                # Check if we should retry
                error_type = self._categorize_error(result.errors)
                if not self.should_retry(error_type):
                    return self._escalate(result, "Error type not retryable")

                # Analyze and fix
                analysis = await error_analyzer(result.errors, context)
                await fix_applier(analysis, context)

                # Wait before retry
                if attempt < self.config.max_retries:
                    await asyncio.sleep(self.config.retry_delay)

            except Exception as e:
                self.attempt_history.append({
                    "attempt": attempt,
                    "success": False,
                    "errors": [str(e)],
                    "duration": time.time() - start_time,
                    "timestamp": datetime.now().isoformat()
                })

                if attempt == self.config.max_retries:
                    return self._escalate(
                        TaskResult(success=False, errors=[str(e)]),
                        f"Max retries ({self.config.max_retries}) exceeded"
                    )

        # Max retries exceeded
        return self._escalate(
            TaskResult(success=False, errors=["Max retries exceeded"]),
            f"Agent tried {self.config.max_retries} times but failed"
        )

    def _categorize_error(self, errors: List[str]) -> str:
        """Categorize error type from error messages"""
        error_text = " ".join(errors).lower()

        if "test" in error_text or "assert" in error_text:
            return "test_failure"
        elif "build" in error_text or "compile" in error_text:
            return "build_error"
        elif "lint" in error_text or "eslint" in error_text:
            return "lint_error"
        elif "security" in error_text or "vulnerability" in error_text:
            return "security_vulnerability"
        elif "rate limit" in error_text or "429" in error_text:
            return "api_rate_limit"
        else:
            return "unknown_error"

    def _escalate(self, result: TaskResult, reason: str) -> TaskResult:
        """Escalate to human review"""
        result.success = False
        result.errors.append(f"ESCALATED: {reason}")
        return result


class ParallelExecutor:
    """Execute multiple tasks in parallel"""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers

    async def execute_parallel(
        self,
        tasks: List[Dict],
        executor_func: Callable,
        context: ExecutionContext
    ) -> Dict[str, TaskResult]:
        """Execute tasks in parallel, respecting dependencies"""

        # Build dependency graph
        task_graph = self._build_dependency_graph(tasks)

        # Execute in waves based on dependencies
        results = {}
        completed = set()

        while len(completed) < len(tasks):
            # Find tasks that can run (dependencies satisfied)
            runnable = [
                t for t in tasks
                if t.get("id", t.get("agent")) not in completed
                and all(dep in completed for dep in t.get("depends_on", []))
            ]

            if not runnable:
                if len(completed) < len(tasks):
                    # Deadlock or circular dependency
                    raise RuntimeError("Circular dependency detected in tasks")
                break

            # Execute runnable tasks in parallel
            wave_results = await self._execute_wave(runnable, executor_func, context)
            results.update(wave_results)

            # Mark completed
            for task in runnable:
                task_id = task.get("id", task.get("agent"))
                completed.add(task_id)

        return results

    async def _execute_wave(
        self,
        tasks: List[Dict],
        executor_func: Callable,
        context: ExecutionContext
    ) -> Dict[str, TaskResult]:
        """Execute a wave of independent tasks"""
        results = {}

        # Create async tasks
        async_tasks = []
        for task in tasks:
            task_id = task.get("id", task.get("agent"))
            async_tasks.append((task_id, executor_func(task, context)))

        # Wait for all to complete
        for task_id, coro in async_tasks:
            try:
                result = await coro
                results[task_id] = result
            except Exception as e:
                results[task_id] = TaskResult(
                    success=False,
                    errors=[str(e)]
                )

        return results

    def _build_dependency_graph(self, tasks: List[Dict]) -> Dict[str, List[str]]:
        """Build dependency graph from tasks"""
        graph = {}
        for task in tasks:
            task_id = task.get("id", task.get("agent"))
            graph[task_id] = task.get("depends_on", [])
        return graph


class ExecutionEngine:
    """Main execution engine for WitMind.AI"""

    def __init__(self, root_path: str):
        self.root = Path(root_path)
        self.parallel_executor = ParallelExecutor()

    async def execute_stage(
        self,
        project_id: str,
        stage_config: Dict,
        approval_mode: ApprovalMode = ApprovalMode.BLOCKING,
        skip_approval: bool = False,
        trust_level: str = "development"
    ) -> Dict:
        """Execute a workflow stage with configured behavior"""

        project_path = self.root / "projects" / "active" / project_id
        stage_name = stage_config.get("stage", "unknown")

        # Determine approval mode from config or parameter
        stage_approval = stage_config.get("approval", {})
        mode = ApprovalMode(stage_approval.get("mode", approval_mode.value))

        # Check if approval can be skipped
        if stage_approval.get("cannot_skip", False):
            skip_approval = False

        # Create context
        context = ExecutionContext(
            project_id=project_id,
            project_path=project_path,
            stage=stage_name,
            agent_id=stage_config.get("agent", "unknown"),
            task=stage_config,
            retry_config=RetryConfig(**stage_config.get("error_handling", {})),
            confidence_config=ConfidenceConfig(**stage_config.get("confidence", {}))
        )

        # Check for parallel execution
        if stage_config.get("parallel", False):
            results = await self._execute_parallel_stage(stage_config, context)
        else:
            results = await self._execute_single_agent(stage_config, context)

        # Handle approval based on mode
        approval_result = await self._handle_approval(
            results, mode, context, skip_approval, stage_approval
        )

        return {
            "stage": stage_name,
            "results": results,
            "approval": approval_result,
            "status": "completed" if approval_result.get("approved") else "pending_approval"
        }

    async def _execute_single_agent(
        self,
        stage_config: Dict,
        context: ExecutionContext
    ) -> TaskResult:
        """Execute a single agent task with retry"""

        retry_loop = RetryLoop(context.retry_config)

        async def task_func(ctx):
            # This would call the actual agent runner
            # For now, return a mock result
            return await self._run_agent(ctx.agent_id, ctx.task, ctx)

        async def error_analyzer(errors, ctx):
            # Analyze errors and return fix plan
            return {"errors": errors, "fix_plan": "auto_fix"}

        async def fix_applier(analysis, ctx):
            # Apply fixes
            pass

        result = await retry_loop.execute_with_retry(
            task_func, error_analyzer, fix_applier, context
        )

        return result

    async def _execute_parallel_stage(
        self,
        stage_config: Dict,
        context: ExecutionContext
    ) -> Dict[str, TaskResult]:
        """Execute parallel tasks"""

        tasks = stage_config.get("tasks", [])

        async def executor_func(task, ctx):
            task_context = ExecutionContext(
                project_id=ctx.project_id,
                project_path=ctx.project_path,
                stage=ctx.stage,
                agent_id=task.get("agent"),
                task=task,
                retry_config=RetryConfig(**task.get("error_handling", {})),
                confidence_config=ctx.confidence_config
            )
            return await self._execute_single_agent(task, task_context)

        results = await self.parallel_executor.execute_parallel(
            tasks, executor_func, context
        )

        return results

    async def _handle_approval(
        self,
        results: Any,
        mode: ApprovalMode,
        context: ExecutionContext,
        skip_approval: bool,
        approval_config: Dict
    ) -> Dict:
        """Handle approval based on mode"""

        # Calculate confidence
        if isinstance(results, TaskResult):
            confidence_calc = ConfidenceCalculator(context.confidence_config)
            confidence = confidence_calc.calculate(results)
        else:
            # Average confidence for parallel results
            confidence_calc = ConfidenceCalculator(context.confidence_config)
            scores = [confidence_calc.calculate(r) for r in results.values()]
            confidence = sum(scores) / len(scores) if scores else 0

        if skip_approval:
            return {
                "approved": True,
                "mode": "skipped",
                "confidence": confidence
            }

        if mode == ApprovalMode.AUTO:
            threshold = approval_config.get("confidence", {}).get("threshold", 0.8)
            auto_approved = confidence >= threshold
            return {
                "approved": auto_approved,
                "mode": "auto",
                "confidence": confidence,
                "threshold": threshold,
                "reason": "Confidence score met threshold" if auto_approved else "Below threshold"
            }

        elif mode == ApprovalMode.ASYNC:
            # Mark for async review but continue
            self._queue_for_review(context, results, confidence)
            return {
                "approved": True,  # Allow continuation
                "mode": "async",
                "confidence": confidence,
                "pending_review": True,
                "review_id": f"review_{context.project_id}_{context.stage}"
            }

        elif mode == ApprovalMode.POST_REVIEW:
            # Continue, queue for later review
            self._queue_for_review(context, results, confidence)
            return {
                "approved": True,
                "mode": "post_review",
                "confidence": confidence,
                "queued_for_review": True
            }

        else:  # BLOCKING
            # Wait for human approval
            return {
                "approved": False,
                "mode": "blocking",
                "confidence": confidence,
                "waiting_for_human": True,
                "approval_request_id": self._create_approval_request(context, results, confidence)
            }

    def _queue_for_review(self, context: ExecutionContext, results: Any, confidence: float):
        """Queue stage results for async review"""
        review_path = context.project_path / ".reviews"
        review_path.mkdir(parents=True, exist_ok=True)

        review_file = review_path / f"{context.stage}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        review_data = {
            "stage": context.stage,
            "agent": context.agent_id,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
            "status": "pending_review",
            "results": str(results)  # Simplified
        }

        with open(review_file, 'w', encoding='utf-8') as f:
            json.dump(review_data, f, indent=2, ensure_ascii=False)

    def _create_approval_request(self, context: ExecutionContext, results: Any, confidence: float) -> str:
        """Create approval request for blocking mode"""
        # This would integrate with ApprovalGate
        request_id = f"approve_{context.project_id}_{context.stage}_{int(time.time())}"
        return request_id

    async def _run_agent(self, agent_id: str, task: Dict, context: ExecutionContext) -> TaskResult:
        """Run an agent (placeholder - would integrate with AgentRunner)"""
        # This is a placeholder - actual implementation would:
        # 1. Load agent configuration
        # 2. Set up LLM router
        # 3. Execute agent with prompts
        # 4. Run tests
        # 5. Return results

        return TaskResult(
            success=True,
            output={"agent": agent_id, "task": "completed"},
            test_results={"all_passed": True, "pass_rate": 1.0}
        )


# Singleton instance
_execution_engine = None


def get_execution_engine(root_path: str = None) -> ExecutionEngine:
    """Get or create the execution engine instance"""
    global _execution_engine
    if _execution_engine is None:
        if root_path is None:
            root_path = os.environ.get('WITMIND_ROOT', str(Path.home() / 'witmind-data'))
        _execution_engine = ExecutionEngine(root_path)
    return _execution_engine
