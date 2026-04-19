"""
Pipeline Context

Shared context for passing data between pipeline stages.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
import numpy as np


class PipelineMode(Enum):
    """Pipeline execution modes"""
    FULL = "full"           # Complete pipeline
    DETECTION_ONLY = "detection_only"
    OCR_ONLY = "ocr_only"
    TRANSLATION_ONLY = "translation_only"
    INPAINT_ONLY = "inpaint_only"


@dataclass
class PipelineContext:
    """
    Shared context passed through the pipeline.

    Stages can read/write any data they need.
    Common keys:
        - image: original image (np.ndarray)
        - mask: combined inpainting mask
        - blocks: list of TextBlock objects
        - source_lang: detected/selected source language
        - target_lang: selected target language
        - config: pipeline configuration dict
    """

    # Core data
    image: Optional[np.ndarray] = None
    blocks: List[Any] = field(default_factory=list)
    mask: Optional[np.ndarray] = None

    # Language settings
    source_lang: str = "Auto"
    target_lang: str = "简体中文"

    # Mode and settings
    mode: PipelineMode = PipelineMode.FULL
    enable_inpaint: bool = True
    enable_render: bool = True

    # Per-stage metadata storage
    _stage_data: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Original file path (for reference)
    original_path: Optional[str] = None

    # User data (free-form)
    extra: Dict[str, Any] = field(default_factory=dict)

    def get_stage_data(self, stage_name: str) -> Dict[str, Any]:
        """Get data stored by a specific stage"""
        return self._stage_data.get(stage_name, {})

    def set_stage_data(self, stage_name: str, key: str, value: Any) -> None:
        """Store data for a specific stage"""
        if stage_name not in self._stage_data:
            self._stage_data[stage_name] = {}
        self._stage_data[stage_name][key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from extra or known fields"""
        if hasattr(self, key):
            return getattr(self, key)
        return self.extra.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value in extra"""
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            self.extra[key] = value

    def has_key(self, key: str) -> bool:
        """Check if a key exists"""
        if hasattr(self, key):
            return True
        return key in self.extra

    def copy(self) -> 'PipelineContext':
        """Create a shallow copy of the context"""
        new_ctx = PipelineContext(
            image=self.image,
            blocks=self.blocks.copy() if self.blocks else [],
            mask=self.mask,
            source_lang=self.source_lang,
            target_lang=self.target_lang,
            mode=self.mode,
            enable_inpaint=self.enable_inpaint,
            enable_render=self.enable_render,
            original_path=self.original_path,
            extra=self.extra.copy(),
        )
        # Deep copy stage data
        for k, v in self._stage_data.items():
            new_ctx._stage_data[k] = v.copy()
        return new_ctx

    def clear_stage_data(self, stage_name: Optional[str] = None) -> None:
        """Clear data for a specific stage, or all if None"""
        if stage_name:
            self._stage_data.pop(stage_name, None)
        else:
            self._stage_data.clear()
