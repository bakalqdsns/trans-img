#!/usr/bin/env python3
"""
Pipeline Orchestration Demo

Demonstrates the new decoupled pipeline architecture.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from modules.pipeline import (
    PipelineOrchestrator,
    PipelineContext,
    PipelineConfig,
    StageConfig,
    DetectionStage,
    OCRStage,
    TranslationStage,
    InpaintingStage,
    RenderingStage,
    create_pipeline,
    PRESET_PIPELINES,
)


def create_dummy_image(size=(800, 600, 3)):
    """Create a dummy image for testing"""
    return np.random.randint(0, 255, size, dtype=np.uint8)


def create_dummy_blocks(count=3):
    """Create dummy text blocks for testing"""
    from utils.textblock import TextBlock

    blocks = []
    for i in range(count):
        block = TextBlock()
        block.RECT = (100 + i * 50, 100 + i * 30, 200, 40)
        block.text = f"Sample text {i}"
        block.translated_text = ""
        blocks.append(block)
    return blocks


def demo_basic_pipeline():
    """Demo: Basic pipeline construction"""
    print("\n" + "="*60)
    print("Demo: Basic Pipeline Construction")
    print("="*60)

    # Create orchestrator
    orchestrator = PipelineOrchestrator()

    # Add stages
    orchestrator.add_stage(DetectionStage("detection"))
    orchestrator.add_stage(OCRStage("ocr"))
    orchestrator.add_stage(TranslationStage("translation"))
    orchestrator.add_stage(InpaintingStage("inpainting"))
    orchestrator.add_stage(RenderingStage("rendering"))

    print(f"\nCreated: {orchestrator}")
    print(f"Stages: {[s.name for s in orchestrator.stages]}")


def demo_config_based_pipeline():
    """Demo: Pipeline from configuration"""
    print("\n" + "="*60)
    print("Demo: Configuration-Based Pipeline")
    print("="*60)

    # Create config
    config = PipelineConfig(
        name="demo",
        stages=[
            StageConfig(name="detection", stage_type="detection", model_name="ctd"),
            StageConfig(name="ocr", stage_type="ocr", model_name="manga_ocr"),
            StageConfig(name="translation", stage_type="translation", model_name="google"),
        ],
        continue_on_error=True,
    )

    # Create pipeline from config
    orchestrator = create_pipeline(config)

    print(f"\nCreated from config: {orchestrator}")
    print(f"Stages: {[s.name for s in orchestrator.stages]}")
    print(f"Config: {config.to_json()}")


def demo_preset_pipelines():
    """Demo: Preset pipeline configurations"""
    print("\n" + "="*60)
    print("Demo: Preset Pipelines")
    print("="*60)

    for name, config in PRESET_PIPELINES.items():
        print(f"\n{name}:")
        print(f"  Stages: {[s.name for s in config.stages]}")
        print(f"  Enable inpaint: {config.enable_inpainting}")


def demo_pipeline_execution():
    """Demo: Pipeline execution (mock mode)"""
    print("\n" + "="*60)
    print("Demo: Pipeline Execution (Mock)")
    print("="*60)

    # Create pipeline
    orchestrator = PipelineOrchestrator({'continue_on_error': True})

    # Add simple stages that just pass through
    class MockStage:
        def __init__(self, name):
            self.name = name
            self.enabled = True

        def process(self, blocks, image, context):
            from modules.pipeline import StageResult, StageStatus
            import time
            start = time.time()
            print(f"  [Stage: {self.name}] Processing {len(blocks)} blocks")
            return StageResult(
                stage_name=self.name,
                status=StageStatus.SUCCESS,
                blocks=blocks,
                image=image,
                duration_ms=(time.time() - start) * 1000
            )

    orchestrator.add_stage(MockStage("detection"))
    orchestrator.add_stage(MockStage("ocr"))
    orchestrator.add_stage(MockStage("translation"))

    # Create context
    context = PipelineContext(
        image=create_dummy_image(),
        blocks=create_dummy_blocks(5),
    )
    context.source_lang = "English"
    context.target_lang = "Chinese"

    print("\nRunning pipeline...")
    result_context = orchestrator.run(context)

    print(f"\nPipeline state: {orchestrator.state.value}")
    print(f"Stats: {orchestrator.stats}")
    print(f"Final blocks: {len(result_context.blocks)}")


def demo_context_sharing():
    """Demo: Context data sharing between stages"""
    print("\n" + "="*60)
    print("Demo: Context Data Sharing")
    print("="*60)

    # Create context
    context = PipelineContext()
    context.set_stage_data("detection", "algorithm", "ctd")
    context.set_stage_data("detection", "confidence_threshold", 0.7)

    # Read back
    detection_data = context.get_stage_data("detection")
    print(f"Detection stage data: {detection_data}")

    # Global data
    context.set("custom_key", "custom_value")
    print(f"Custom data: {context.get('custom_key')}")


def demo_error_handling():
    """Demo: Error handling and recovery"""
    print("\n" + "="*60)
    print("Demo: Error Handling")
    print("="*60)

    class FailingStage:
        def __init__(self, name, fail_count=1):
            self.name = name
            self.enabled = True
            self.fail_count = fail_count
            self.attempts = 0

        def process(self, blocks, image, context):
            from modules.pipeline import StageResult, StageStatus
            import time
            self.attempts += 1
            start = time.time()

            if self.attempts <= self.fail_count:
                print(f"  [Stage: {self.name}] Simulating failure (attempt {self.attempts})")
                return StageResult(
                    stage_name=self.name,
                    status=StageStatus.FAILED,
                    blocks=blocks,
                    error="Simulated failure",
                    duration_ms=(time.time() - start) * 1000
                )

            print(f"  [Stage: {self.name}] Succeeded on attempt {self.attempts}")
            return StageResult(
                stage_name=self.name,
                status=StageStatus.SUCCESS,
                blocks=blocks,
                duration_ms=(time.time() - start) * 1000
            )

    orchestrator = PipelineOrchestrator({'continue_on_error': True, 'max_retries': 2})
    orchestrator.add_stage(FailingStage("unreliable", fail_count=1))
    orchestrator.add_stage(FailingStage("reliable"))

    context = PipelineContext(
        image=create_dummy_image(),
        blocks=create_dummy_blocks(2),
    )

    print("\nRunning with error handling...")
    result = orchestrator.run(context)
    print(f"\nFinal state: {orchestrator.state.value}")
    print(f"Stats: success_rate={orchestrator.stats.success_rate:.1%}")


def demo_hooks():
    """Demo: Pipeline hooks"""
    print("\n" + "="*60)
    print("Demo: Pipeline Hooks")
    print("="*60)

    orchestrator = PipelineOrchestrator()

    # Add hooks
    pre_hook_calls = []
    post_hook_calls = []

    def pre_hook(context):
        pre_hook_calls.append(True)
        print(f"  [Pre-hook] Starting pipeline")

    def post_hook(context, results):
        post_hook_calls.append(True)
        print(f"  [Post-hook] Pipeline completed with {len(results)} stage results")

    orchestrator.add_pre_run_hook(pre_hook)
    orchestrator.add_post_run_hook(post_hook)

    # Add simple stage
    class SimpleStage:
        def __init__(self, name):
            self.name = name
            self.enabled = True

        def process(self, blocks, image, context):
            from modules.pipeline import StageResult, StageStatus
            return StageResult(stage_name=self.name, status=StageStatus.SUCCESS, blocks=blocks)

    orchestrator.add_stage(SimpleStage("test"))

    context = PipelineContext(image=create_dummy_image(), blocks=create_dummy_blocks(1))
    orchestrator.run(context)

    print(f"\nPre-hook calls: {len(pre_hook_calls)}")
    print(f"Post-hook calls: {len(post_hook_calls)}")


if __name__ == "__main__":
    print("Pipeline Orchestration Layer Demo")
    print("=" * 60)

    # Run demos
    demo_basic_pipeline()
    demo_config_based_pipeline()
    demo_preset_pipelines()
    demo_pipeline_execution()
    demo_context_sharing()
    demo_error_handling()
    demo_hooks()

    print("\n" + "=" * 60)
    print("All demos completed!")
