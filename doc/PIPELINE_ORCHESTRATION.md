# Pipeline Orchestration Layer

## 概述

Pipeline Orchestration Layer 是 BallonsTranslator 的核心编排系统，将原本高耦合的 Pipeline 解耦为独立的 Stage 阶段。

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    PipelineOrchestrator                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │Detection│→ │  OCR    │→ │Translate│→ │Inpaint  │→ ...   │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │
│       ↑            ↑            ↑            ↑               │
│       └────────────┴────────────┴────────────┘               │
│                    PipelineContext                           │
│              (Shared data between stages)                    │
└─────────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. PipelineStage

所有阶段的基类：

```python
class MyStage(PipelineStage):
    def process(self, blocks, image, context) -> StageResult:
        # 处理逻辑
        return StageResult(...)
```

### 2. PipelineContext

阶段间共享数据：

```python
context = PipelineContext()
context.image = img
context.blocks = text_blocks
context.source_lang = "Japanese"
context.target_lang = "Chinese"

# 阶段间共享数据
context.set_stage_data("detection", "algorithm", "ctd")
context.get_stage_data("detection")  # {"algorithm": "ctd"}
```

### 3. PipelineOrchestrator

编排器，负责执行顺序和错误处理：

```python
orchestrator = PipelineOrchestrator()
orchestrator.add_stage(DetectionStage("detection"))
orchestrator.add_stage(OCRStage("ocr"))
orchestrator.add_stage(TranslationStage("translation"))

context = PipelineContext(image=img, blocks=blocks)
result_context = orchestrator.run(context)
```

## 使用示例

### 基础用法

```python
from modules.pipeline import (
    PipelineOrchestrator,
    PipelineContext,
    DetectionStage,
    OCRStage,
    TranslationStage,
    InpaintingStage,
)

# 创建编排器
orchestrator = PipelineOrchestrator({'continue_on_error': True})

# 添加阶段
orchestrator.add_stage(DetectionStage("detection"))
orchestrator.add_stage(OCRStage("ocr"))
orchestrator.add_stage(TranslationStage("translation"))
orchestrator.add_stage(InpaintingStage("inpainting"))

# 执行
context = PipelineContext(image=img, blocks=[])
result = orchestrator.run(context)
```

### 配置驱动

```python
from modules.pipeline import PipelineConfig, StageConfig, create_pipeline

config = PipelineConfig(
    name="my_pipeline",
    stages=[
        StageConfig(name="detection", stage_type="detection", model_name="ctd"),
        StageConfig(name="ocr", stage_type="ocr", model_name="manga_ocr"),
        StageConfig(name="translation", stage_type="translation", model_name="deepl"),
    ]
)

orchestrator = create_pipeline(config)
```

### 预设配置

```python
from modules.pipeline import PRESET_PIPELINES

fast_pipeline = create_pipeline(PRESET_PIPELINES["fast"])
quality_pipeline = create_pipeline(PRESET_PIPELINES["quality"])
```

## 错误处理

### 继续执行

```python
orchestrator = PipelineOrchestrator({'continue_on_error': True})
```

### 重试机制

```python
orchestrator = PipelineOrchestrator({'max_retries': 2})
```

### 错误处理器

```python
def my_error_handler(context, stage, exception):
    # 自定义错误处理
    return StageResult(stage_name=stage.name, status=StageStatus.SKIPPED)

orchestrator.set_error_handler("ocr", my_error_handler)
```

## Hooks

```python
def pre_run(context):
    print("Pipeline starting")

def post_run(context, results):
    print(f"Completed: {len(results)} stages")

orchestrator.add_pre_run_hook(pre_run)
orchestrator.add_post_run_hook(post_run)
```

## 文件结构

```
modules/pipeline/
├── __init__.py       # 导出和工厂函数
├── orchestrator.py   # PipelineOrchestrator
├── stage.py          # PipelineStage 基类
├── context.py        # PipelineContext
├── config.py         # 配置类
└── adapters.py       # 现有模块适配器
```

## 迁移指南

### 旧代码

```python
# 高耦合
module_manager.run_pipeline(image, mode="full")
```

### 新代码

```python
# 解耦
from modules.pipeline import create_pipeline, PRESET_PIPELINES

orchestrator = create_pipeline(PRESET_PIPELINES["quality"])
context = PipelineContext(image=image)
result = orchestrator.run(context)
```

## 下一步

- [ ] Stage Layer 实现：具体阶段逻辑抽取
- [ ] TextBlock 重构：Region + TextContent + TextStyle
- [ ] 单元测试完善
