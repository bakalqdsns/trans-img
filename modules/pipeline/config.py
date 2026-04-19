"""
Pipeline Configuration

Configuration classes for pipeline and stages.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class StageType(Enum):
    """Standard pipeline stage types"""
    DETECTION = "detection"
    OCR = "ocr"
    TRANSLATION = "translation"
    INPAINTING = "inpainting"
    RENDERING = "rendering"


@dataclass
class StageConfig:
    """Configuration for a single pipeline stage"""
    name: str
    stage_type: str
    enabled: bool = True
    model_name: Optional[str] = None
    model_config: Dict[str, Any] = field(default_factory=dict)
    runtime_config: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StageConfig':
        """Create from dictionary"""
        return cls(
            name=data.get('name', data.get('type', 'unknown')),
            stage_type=data.get('type', 'unknown'),
            enabled=data.get('enabled', True),
            model_name=data.get('model'),
            model_config=data.get('model_config', {}),
            runtime_config=data.get('runtime_config', {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'type': self.stage_type,
            'enabled': self.enabled,
            'model': self.model_name,
            'model_config': self.model_config,
            'runtime_config': self.runtime_config,
        }


@dataclass
class PipelineConfig:
    """
    Pipeline configuration.

    Defines the structure and settings for a complete pipeline.
    """

    name: str = "default"
    stages: List[StageConfig] = field(default_factory=list)

    # Global settings
    continue_on_error: bool = True
    max_retries: int = 1
    parallel_execution: bool = False  # Future: run independent stages in parallel

    # Default language settings
    default_source_lang: str = "Auto"
    default_target_lang: str = "简体中文"

    # Feature flags
    enable_inpainting: bool = True
    enable_rendering: bool = True
    enable_cache: bool = True

    # Model registry integration
    use_model_registry: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PipelineConfig':
        """Create from dictionary"""
        stages = [StageConfig.from_dict(s) for s in data.get('stages', [])]
        return cls(
            name=data.get('name', 'default'),
            stages=stages,
            continue_on_error=data.get('continue_on_error', True),
            max_retries=data.get('max_retries', 1),
            parallel_execution=data.get('parallel_execution', False),
            default_source_lang=data.get('default_source_lang', 'Auto'),
            default_target_lang=data.get('default_target_lang', '简体中文'),
            enable_inpainting=data.get('enable_inpainting', True),
            enable_rendering=data.get('enable_rendering', True),
            enable_cache=data.get('enable_cache', True),
            use_model_registry=data.get('use_model_registry', True),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'stages': [s.to_dict() for s in self.stages],
            'continue_on_error': self.continue_on_error,
            'max_retries': self.max_retries,
            'parallel_execution': self.parallel_execution,
            'default_source_lang': self.default_source_lang,
            'default_target_lang': self.default_target_lang,
            'enable_inpainting': self.enable_inpainting,
            'enable_rendering': self.enable_rendering,
            'enable_cache': self.enable_cache,
            'use_model_registry': self.use_model_registry,
        }

    def get_stage(self, name: str) -> Optional[StageConfig]:
        """Get a stage configuration by name"""
        for stage in self.stages:
            if stage.name == name:
                return stage
        return None

    def add_stage(self, stage: StageConfig) -> 'PipelineConfig':
        """Add a stage configuration"""
        self.stages.append(stage)
        return self

    def remove_stage(self, name: str) -> Optional[StageConfig]:
        """Remove a stage configuration"""
        for i, stage in enumerate(self.stages):
            if stage.name == name:
                return self.stages.pop(i)
        return None

    @classmethod
    def from_json(cls, json_str: str) -> 'PipelineConfig':
        """Create from JSON string"""
        import json
        return cls.from_dict(json.loads(json_str))

    def to_json(self) -> str:
        """Convert to JSON string"""
        import json
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> 'PipelineConfig':
        """Load configuration from JSON file"""
        import json
        with open(filepath, 'r', encoding='utf-8') as f:
            return cls.from_dict(json.load(f))

    def save_to_file(self, filepath: str) -> None:
        """Save configuration to JSON file"""
        import json
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)


# Predefined pipeline configurations
PRESET_PIPELINES = {
    "fast": PipelineConfig(
        name="fast",
        stages=[
            StageConfig(name="detection", stage_type="detection", model_name="fast_ctd"),
            StageConfig(name="ocr", stage_type="ocr", model_name="manga_ocr"),
            StageConfig(name="translation", stage_type="translation", model_name="google"),
        ],
        enable_inpainting=False,
    ),
    "quality": PipelineConfig(
        name="quality",
        stages=[
            StageConfig(name="detection", stage_type="detection", model_name="ctd"),
            StageConfig(name="ocr", stage_type="ocr", model_name="paddle_ocr"),
            StageConfig(name="translation", stage_type="translation", model_name="deepl"),
            StageConfig(name="inpainting", stage_type="inpainting", model_name="lama"),
            StageConfig(name="rendering", stage_type="rendering"),
        ],
    ),
    "debug": PipelineConfig(
        name="debug",
        stages=[
            StageConfig(name="detection", stage_type="detection"),
            StageConfig(name="ocr", stage_type="ocr"),
            StageConfig(name="translation", stage_type="translation"),
            StageConfig(name="inpainting", stage_type="inpainting"),
        ],
        continue_on_error=False,
        max_retries=0,
    ),
}
