"""
Pipeline Stage Base

Base class and interfaces for all pipeline stages.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
import time
import logging

from utils.textblock import TextBlock


class StageStatus(Enum):
    """Stage execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageResult:
    """Result from a stage execution"""
    stage_name: str
    status: StageStatus
    blocks: List[TextBlock] = field(default_factory=list)
    image: Any = None  # Optional processed image
    error: Optional[str] = None
    duration_ms: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.status == StageStatus.SUCCESS

    def merge_metadata(self, other: 'StageResult') -> None:
        """Merge metadata from another result (e.g., partial failures)"""
        self.metadata.update(other.metadata)
        if other.error and not self.error:
            self.error = other.error


class PipelineStage(ABC):
    """
    Abstract base class for pipeline stages.

    A stage processes TextBlocks and optionally an image,
    returning modified blocks and/or a modified image.
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"pipeline.{name}")
        self._enabled = True
        self._hooks: Dict[str, List[Callable]] = {
            'pre': [],
            'post': [],
            'error': [],
        }

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    def add_hook(self, stage: str, callback: Callable) -> None:
        """Add a hook callback (pre/post/error)"""
        if stage in self._hooks:
            self._hooks[stage].append(callback)

    def remove_hook(self, stage: str, callback: Callable) -> None:
        """Remove a hook callback"""
        if stage in self._hooks:
            self._hooks[stage].remove(callback)

    def _run_hooks(self, stage: str, context: 'PipelineContext', result: Optional[StageResult] = None) -> None:
        """Run hook callbacks"""
        for callback in self._hooks[stage]:
            try:
                callback(context, result)
            except Exception as e:
                self.logger.warning(f"Hook error in {stage}: {e}")

    @abstractmethod
    def process(self, blocks: List[TextBlock], image: Any, context: 'PipelineContext') -> StageResult:
        """
        Process blocks and optionally image.

        Args:
            blocks: List of TextBlock objects to process
            image: Original image (may be modified)
            context: Shared pipeline context

        Returns:
            StageResult with processed blocks and/or image
        """
        pass

    def validate_config(self) -> bool:
        """Validate stage configuration. Return True if valid."""
        return True


class CompositeStage(PipelineStage):
    """
    A stage that wraps multiple sub-stages.

    Useful for combining similar operations (e.g., multiple OCR attempts,
    fallback translation engines, etc.)
    """

    def __init__(self, name: str, stages: List[PipelineStage], config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.stages = stages
        self._fallback_mode = config.get('fallback_mode', False) if config else False

    @property
    def fallback_mode(self) -> bool:
        return self._fallback_mode

    @fallback_mode.setter
    def fallback_mode(self, value: bool) -> None:
        self._fallback_mode = value
        for stage in self.stages:
            if hasattr(stage, 'fallback_mode'):
                stage.fallback_mode = value

    def process(self, blocks: List[TextBlock], image: Any, context: 'PipelineContext') -> StageResult:
        """Process using sub-stages, with optional fallback"""
        start_time = time.time()
        result = StageResult(stage_name=self.name, status=StageStatus.RUNNING, blocks=blocks)

        if not self.stages:
            result.status = StageStatus.SKIPPED
            return result

        if self._fallback_mode:
            # Try each stage until one succeeds
            for stage in self.stages:
                if not stage.enabled:
                    continue
                try:
                    self._run_hooks('pre', context)
                    sub_result = stage.process(blocks, image, context)
                    result.merge_metadata(sub_result)
                    if sub_result.success:
                        result.blocks = sub_result.blocks
                        result.image = sub_result.image
                        result.status = StageStatus.SUCCESS
                        self._run_hooks('post', context, result)
                        return result
                except Exception as e:
                    self.logger.warning(f"Stage {stage.name} failed: {e}")
                    result.metadata[f"{stage.name}_error"] = str(e)
                    continue
            result.status = StageStatus.FAILED
            result.error = "All fallback stages failed"
        else:
            # Run all stages sequentially
            current_blocks = blocks
            current_image = image
            for stage in self.stages:
                if not stage.enabled:
                    continue
                try:
                    self._run_hooks('pre', context)
                    sub_result = stage.process(current_blocks, current_image, context)
                    result.merge_metadata(sub_result)
                    if not sub_result.success:
                        self.logger.warning(f"Stage {stage.name} failed, continuing with next")
                    current_blocks = sub_result.blocks
                    if sub_result.image is not None:
                        current_image = sub_result.image
                except Exception as e:
                    self.logger.warning(f"Stage {stage.name} error: {e}")
                    result.metadata[f"{stage.name}_error"] = str(e)

            result.blocks = current_blocks
            result.image = current_image
            result.status = StageStatus.SUCCESS

        self._run_hooks('post', context, result)
        result.duration_ms = (time.time() - start_time) * 1000
        return result


# Stage type registry for dynamic instantiation
_STAGE_REGISTRY: Dict[str, type] = {}


def register_stage(stage_type: str):
    """Decorator to register a stage class"""
    def decorator(cls):
        _STAGE_REGISTRY[stage_type] = cls
        return cls
    return decorator


def create_stage(stage_type: str, name: str, config: Optional[Dict[str, Any]] = None) -> PipelineStage:
    """Factory function to create a stage by type"""
    if stage_type not in _STAGE_REGISTRY:
        raise ValueError(f"Unknown stage type: {stage_type}. Available: {list(_STAGE_REGISTRY.keys())}")
    return _STAGE_REGISTRY[stage_type](name=name, config=config)
