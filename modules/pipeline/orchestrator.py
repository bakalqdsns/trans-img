"""
Pipeline Orchestrator

Coordinates the execution of all pipeline stages.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
import logging
import time

from .stage import PipelineStage, StageResult, StageStatus, CompositeStage
from .context import PipelineContext, PipelineMode
from utils.textblock import TextBlock


class PipelineState(Enum):
    """Overall pipeline state"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PipelineStats:
    """Pipeline execution statistics"""
    total_duration_ms: float = 0
    stage_stats: Dict[str, float] = field(default_factory=dict)
    blocks_processed: int = 0
    blocks_failed: int = 0

    @property
    def success_rate(self) -> float:
        total = self.blocks_processed + self.blocks_failed
        return self.blocks_processed / total if total > 0 else 0.0


class PipelineOrchestrator:
    """
    Main pipeline orchestrator.

    Manages stage execution, data flow, and error handling.

    Usage:
        orchestrator = PipelineOrchestrator()
        orchestrator.add_stage(detection_stage)
        orchestrator.add_stage(ocr_stage)
        orchestrator.add_stage(translation_stage)
        orchestrator.add_stage(inpainting_stage)

        context = PipelineContext(image=img, blocks=blocks)
        result = orchestrator.run(context)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger("pipeline.orchestrator")
        self.config = config or {}

        # Stages in execution order
        self._stages: List[PipelineStage] = []
        self._stage_map: Dict[str, PipelineStage] = {}

        # State
        self._state = PipelineState.IDLE
        self._stats = PipelineStats()
        self._current_stage_index = -1

        # Global hooks
        self._pre_run_hooks: List[Callable] = []
        self._post_run_hooks: List[Callable] = []
        self._error_handlers: Dict[str, Callable] = {}

        # Fallback configuration
        self._continue_on_error = self.config.get('continue_on_error', True)
        self._max_retries = self.config.get('max_retries', 1)

    @property
    def state(self) -> PipelineState:
        return self._state

    @property
    def stats(self) -> PipelineStats:
        return self._stats

    @property
    def stages(self) -> List[PipelineStage]:
        return self._stages.copy()

    def add_stage(self, stage: PipelineStage, position: Optional[int] = None) -> 'PipelineOrchestrator':
        """
        Add a stage to the pipeline.

        Args:
            stage: The stage to add
            position: Optional position index (append by default)

        Returns:
            self for chaining
        """
        if stage.name in self._stage_map:
            raise ValueError(f"Stage with name '{stage.name}' already exists")

        if position is None:
            self._stages.append(stage)
        else:
            self._stages.insert(position, stage)

        self._stage_map[stage.name] = stage
        self.logger.debug(f"Added stage: {stage.name}")
        return self

    def remove_stage(self, name: str) -> Optional[PipelineStage]:
        """Remove a stage by name"""
        stage = self._stage_map.pop(name, None)
        if stage:
            self._stages.remove(stage)
            self.logger.debug(f"Removed stage: {stage.name}")
        return stage

    def get_stage(self, name: str) -> Optional[PipelineStage]:
        """Get a stage by name"""
        return self._stage_map.get(name)

    def clear_stages(self) -> 'PipelineOrchestrator':
        """Remove all stages"""
        self._stages.clear()
        self._stage_map.clear()
        return self

    def add_pre_run_hook(self, hook: Callable) -> 'PipelineOrchestrator':
        """Add a hook to run before pipeline execution"""
        self._pre_run_hooks.append(hook)
        return self

    def add_post_run_hook(self, hook: Callable) -> 'PipelineOrchestrator':
        """Add a hook to run after pipeline execution"""
        self._post_run_hooks.append(hook)
        return self

    def set_error_handler(self, stage_name: str, handler: Callable) -> 'PipelineOrchestrator':
        """
        Set an error handler for a specific stage.

        Handler signature: (context, stage, exception) -> StageResult
        """
        self._error_handlers[stage_name] = handler
        return self

    def run(self, context: PipelineContext, start_stage: Optional[str] = None,
            end_stage: Optional[str] = None) -> PipelineContext:
        """
        Execute the pipeline.

        Args:
            context: Pipeline context with input data
            start_stage: Optional stage name to start from
            end_stage: Optional stage name to end at

        Returns:
            Modified context after all stages
        """
        if not self._stages:
            self.logger.warning("No stages configured")
            return context

        self._state = PipelineState.RUNNING
        self._stats = PipelineStats()
        start_time = time.time()

        # Determine stage range
        start_idx = 0
        end_idx = len(self._stages)

        if start_stage:
            start_idx = next((i for i, s in enumerate(self._stages) if s.name == start_stage), 0)

        if end_stage:
            end_idx = next((i + 1 for i, s in enumerate(self._stages) if s.name == end_stage), len(self._stages))

        # Run pre-run hooks
        for hook in self._pre_run_hooks:
            try:
                hook(context)
            except Exception as e:
                self.logger.warning(f"Pre-run hook error: {e}")

        # Execute stages
        current_blocks = context.blocks
        current_image = context.image
        stage_results: Dict[str, StageResult] = {}

        for i in range(start_idx, end_idx):
            stage = self._stages[i]
            self._current_stage_index = i

            if not stage.enabled:
                self.logger.debug(f"Skipping disabled stage: {stage.name}")
                continue

            # Check if we should skip this stage based on mode
            if context.mode != PipelineMode.FULL:
                if context.mode == PipelineMode.DETECTION_ONLY and stage.name != "detection":
                    continue
                if context.mode == PipelineMode.OCR_ONLY and stage.name != "ocr":
                    continue
                if context.mode == PipelineMode.TRANSLATION_ONLY and stage.name != "translation":
                    continue
                if context.mode == PipelineMode.INPAINT_ONLY and stage.name != "inpainting":
                    continue

            self.logger.info(f"Running stage: {stage.name}")

            # Execute stage with retries
            result = self._execute_stage_with_retries(stage, current_blocks, current_image, context)

            stage_results[stage.name] = result
            self._stats.stage_stats[stage.name] = result.duration_ms

            if result.success:
                current_blocks = result.blocks
                if result.image is not None:
                    current_image = result.image
                self._stats.blocks_processed = len(current_blocks)
            else:
                self._stats.blocks_failed = len(current_blocks)
                if not self._continue_on_error:
                    self.logger.error(f"Stage {stage.name} failed, stopping pipeline")
                    self._state = PipelineState.FAILED
                    break

            # Store stage result in context
            context.set_stage_data(stage.name, 'result', result)

        # Update context with final results
        context.blocks = current_blocks
        context.image = current_image

        # Complete
        self._stats.total_duration_ms = (time.time() - start_time) * 1000
        self._state = PipelineState.COMPLETED if self._state == PipelineState.RUNNING else self._state

        # Run post-run hooks
        for hook in self._post_run_hooks:
            try:
                hook(context, stage_results)
            except Exception as e:
                self.logger.warning(f"Post-run hook error: {e}")

        self.logger.info(f"Pipeline completed in {self._stats.total_duration_ms:.1f}ms")
        return context

    def _execute_stage_with_retries(self, stage: PipelineStage, blocks: List[TextBlock],
                                    image: Any, context: PipelineContext) -> StageResult:
        """Execute a stage with retry logic"""
        last_error = None

        for attempt in range(self._max_retries + 1):
            try:
                return stage.process(blocks, image, context)
            except Exception as e:
                last_error = e
                self.logger.warning(f"Stage {stage.name} attempt {attempt + 1} failed: {e}")

                # Run error handler if available
                if stage.name in self._error_handlers:
                    try:
                        handler = self._error_handlers[stage.name]
                        return handler(context, stage, e)
                    except Exception as handler_error:
                        self.logger.error(f"Error handler for {stage.name} failed: {handler_error}")

        # All retries exhausted
        return StageResult(
            stage_name=stage.name,
            status=StageStatus.FAILED,
            blocks=blocks,
            error=str(last_error),
            duration_ms=0
        )

    def pause(self) -> 'PipelineOrchestrator':
        """Pause pipeline execution (for future use)"""
        self._state = PipelineState.PAUSED
        return self

    def resume(self) -> 'PipelineOrchestrator':
        """Resume pipeline execution (for future use)"""
        if self._state == PipelineState.PAUSED:
            self._state = PipelineState.RUNNING
        return self

    def get_pipeline_info(self) -> Dict[str, Any]:
        """Get information about the configured pipeline"""
        return {
            'state': self._state.value,
            'stage_count': len(self._stages),
            'stages': [s.name for s in self._stages],
            'config': self.config,
        }

    def __repr__(self) -> str:
        return f"PipelineOrchestrator(stages={len(self._stages)}, state={self._state.value})"
