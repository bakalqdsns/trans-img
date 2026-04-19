"""
Pipeline Orchestration Layer

Provides a flexible, decoupled pipeline system for image translation:
- Text Detection → OCR → Translation → Inpainting → Text Rendering

Each stage is independent and communicates via a shared context.
"""

from .orchestrator import PipelineOrchestrator, PipelineContext, PipelineStage, StageResult
from .config import PipelineConfig, StageConfig, PRESET_PIPELINES
from .adapters import (
    DetectionStage,
    OCRStage,
    TranslationStage,
    InpaintingStage,
    RenderingStage,
)

__all__ = [
    # Core
    'PipelineOrchestrator',
    'PipelineContext',
    'PipelineStage',
    'StageResult',
    # Config
    'PipelineConfig',
    'StageConfig',
    'PRESET_PIPELINES',
    # Adapters
    'DetectionStage',
    'OCRStage',
    'TranslationStage',
    'InpaintingStage',
    'RenderingStage',
    # Factory
    'create_pipeline',
]


def create_pipeline(config: PipelineConfig) -> PipelineOrchestrator:
    """
    Create a PipelineOrchestrator from configuration.

    Args:
        config: PipelineConfig defining stages and settings

    Returns:
        Configured PipelineOrchestrator instance
    """
    from .stage import create_stage

    orchestrator = PipelineOrchestrator({
        'continue_on_error': config.continue_on_error,
        'max_retries': config.max_retries,
    })

    for stage_config in config.stages:
        if not stage_config.enabled:
            continue

        stage = create_stage(stage_config.stage_type, stage_config.name, {
            **stage_config.runtime_config,
            'model_name': stage_config.model_name,
        })
        orchestrator.add_stage(stage)

    return orchestrator
