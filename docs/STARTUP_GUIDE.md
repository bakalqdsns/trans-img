# 模型注册表启动方式指南

## 概述

本文档说明如何在BallonsTranslator应用中启动和初始化模型注册表解耦系统。

## 启动流程

### 1. 自动启动（推荐）

系统已配置为自动启动，无需额外操作。在导入 `modules` 包时，会自动执行初始化：

```python
# 在应用启动时（如 launch.py 或 mainwindow.py 中）
from modules import init_model_registry

# 可选：显式调用初始化（如果需要在特定时机初始化）
init_model_registry()
```

### 2. 启动时发生了什么

```
应用启动
    ↓
导入 modules 包
    ↓
执行 modules/__init__.py
    ↓
调用 init_model_registry()
    ↓
迁移原有模型到新的注册表
    - TEXTDETECTORS → ModelType.TEXT_DETECTOR
    - OCR → ModelType.OCR
    - INPAINTERS → ModelType.INPAINTER
    - TRANSLATORS → ModelType.TRANSLATOR
    ↓
加载自定义模型
    - 扫描 config/custom_models/*.json
    - 解析并注册到注册表
    ↓
系统就绪
```

## 不同场景的启动方式

### 场景一：普通启动（现有代码无需修改）

**文件**: `launch.py` 或应用入口文件

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入模块（自动触发初始化）
from modules import (
    GET_VALID_OCR,
    GET_VALID_TRANSLATORS,
    GET_VALID_TEXTDETECTORS,
    GET_VALID_INPAINTERS,
)

# 此时模型注册表已初始化完成
print(f"可用OCR模型: {GET_VALID_OCR()}")
print(f"可用翻译器: {GET_VALID_TRANSLATORS()}")

# 继续启动应用...
from ui.mainwindow import MainWindow
# ...
```

### 场景二：延迟初始化（控制启动时机）

**文件**: 需要控制初始化时机的场景

```python
# 在 modules/__init__.py 中禁用自动初始化
# 注释掉以下行:
# init_model_registry()

# 在应用代码中手动控制初始化时机
def main():
    # 1. 先加载配置
    from utils.config import load_config
    load_config()
    
    # 2. 初始化模型注册表
    from modules import init_model_registry
    init_model_registry()
    
    # 3. 启动UI
    from ui.mainwindow import MainWindow
    # ...
```

### 场景三：无GUI环境（脚本/批处理）

**文件**: 批处理脚本或命令行工具

```python
#!/usr/bin/env python3
"""命令行批处理工具 - 无GUI环境"""

import sys
from pathlib import Path

# 设置项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入核心模块（不依赖Qt）
from modules import (
    model_registry,
    ModelType,
    GET_VALID_OCR,
)

# 注册表已自动初始化

def list_models():
    """列出所有可用模型"""
    print("=" * 60)
    print("可用模型列表")
    print("=" * 60)
    
    for model_type in ModelType:
        models = model_registry.get_model_definitions(model_type)
        print(f"\n{model_type.value.upper()}:")
        for key, definition in models.items():
            provider = "🔧" if definition.provider.value == "custom" else "📦"
            print(f"  {provider} {definition.name} ({key})")

def add_model_from_json(json_path: str):
    """从JSON文件添加模型"""
    import json
    from modules import ModelDefinition
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    definition = ModelDefinition.from_dict(data)
    model_registry.register_model(definition)
    print(f"已添加模型: {definition.name}")

if __name__ == "__main__":
    # 无需显式初始化，导入时已自动完成
    list_models()
```

### 场景四：测试环境

**文件**: `tests/test_*.py`

```python
#!/usr/bin/env python3
"""测试脚本"""

import sys
from pathlib import Path

# 设置路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 方式一：使用自动初始化
from modules import model_registry, ModelType

# 方式二：独立测试（不依赖完整模块链）
import importlib.util
spec = importlib.util.spec_from_file_location(
    "model_registry",
    project_root / "modules" / "model_registry.py"
)
model_registry_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model_registry_module)

# 创建独立的注册表实例（测试用）
registry = model_registry_module.ModelRegistry.__new__(
    model_registry_module.ModelRegistry
)
registry._initialized = True
registry._definitions = {
    mt: {} for mt in model_registry_module.ModelType
}
```

## 配置面板集成

### 方式一：使用新的集成组件（推荐）

**文件**: `ui/configpanel.py`

```python
from modules import (
    IntegratedTextDetectConfigWidget,
    IntegratedOCRConfigWidget,
    IntegratedInpaintConfigWidget,
    IntegratedTranslatorConfigWidget,
)

class ConfigPanel(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 使用新的集成配置组件
        self.detect_config_panel = IntegratedTextDetectConfigWidget(
            self.tr('Detector'),
            scrollWidget=self
        )
        self.detect_config_panel.detector_changed.connect(self.setTextDetector)
        
        self.ocr_config_panel = IntegratedOCRConfigWidget(
            self.tr('OCR'),
            scrollWidget=self
        )
        self.ocr_config_panel.ocr_changed.connect(self.setOCR)
        
        self.inpaint_config_panel = IntegratedInpaintConfigWidget(
            self.tr('Inpainter'),
            scrollWidget=self
        )
        self.inpaint_config_panel.inpainter_changed.connect(self.setInpainter)
        
        self.trans_config_panel = IntegratedTranslatorConfigWidget(
            self.tr('Translator'),
            scrollWidget=self
        )
        self.trans_config_panel.translator_changed.connect(self.setTranslator)
```

### 方式二：保留原有组件（兼容性）

原有代码无需修改，自动获得新功能：

```python
# 原有代码保持不变
from .module_parse_widgets import (
    InpaintConfigPanel,
    TextDetectConfigPanel,
    TranslatorConfigPanel,
    OCRConfigPanel,
)

# 在 ModuleManager.setupThread 中:
translator_params = merge_config_module_params(
    cfg_module.translator_params,
    GET_VALID_TRANSLATORS(),  # 现在返回新注册表中的模型
    TRANSLATORS.get
)
```

## 自定义模型加载目录

### 默认目录

```
config/custom_models/
```

### 修改加载目录

```python
from modules import model_registry
from pathlib import Path

# 修改自定义模型目录
model_registry._custom_models_dir = Path("/path/to/custom/models")
model_registry._load_custom_models()  # 重新加载
```

## 启动时序图

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   应用入口   │     │  modules包  │     │ model_adapter│     │ model_registry│
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │                   │
       │  1. import modules │                   │                   │
       │──────────────────>│                   │                   │
       │                   │                   │                   │
       │                   │  2. from model_adapter import ...      │
       │                   │───────────────────────────────────────>│
       │                   │                   │                   │
       │                   │                   │  3. 创建ModelAdapter
       │                   │                   │──────────────────>│
       │                   │                   │                   │
       │                   │  4. init_model_registry()              │
       │                   │──────────────────>│                   │
       │                   │                   │                   │
       │                   │                   │  5. migrate_all_modules()
       │                   │                   │                   │
       │                   │                   │  6. 从原有Registry迁移
       │                   │                   │  TEXTDETECTORS → 新注册表
       │                   │                   │  OCR → 新注册表
       │                   │                   │  INPAINTERS → 新注册表
       │                   │                   │  TRANSLATORS → 新注册表
       │                   │                   │                   │
       │                   │                   │  7. register_model()
       │                   │                   │──────────────────>│
       │                   │                   │                   │
       │                   │                   │  8. _load_custom_models()
       │                   │                   │──────────────────>│
       │                   │                   │                   │
       │                   │                   │  9. 扫描JSON文件
       │                   │                   │  10. 解析并注册
       │                   │                   │                   │
       │  11. 初始化完成    │                   │                   │
       │<──────────────────│                   │                   │
       │                   │                   │                   │
       │  12. 启动UI       │                   │                   │
       │──────────────────────────────────────────────────────────>│
       │                   │                   │                   │
```

## 故障排查

### 问题1：模型未显示

**症状**: 自定义模型未出现在列表中

**检查**:
```python
from modules import model_registry, ModelType

# 检查是否已注册
exists = model_registry.model_exists(ModelType.OCR, "my_model")
print(f"模型存在: {exists}")

# 检查所有模型
all_models = model_registry.get_model_keys(ModelType.OCR)
print(f"所有OCR模型: {all_models}")

# 检查自定义模型目录
print(f"自定义模型目录: {model_registry._custom_models_dir}")
print(f"目录存在: {model_registry._custom_models_dir.exists()}")
```

### 问题2：初始化失败

**症状**: 导入modules时出现错误

**解决**:
```python
# 禁用自动初始化，手动控制
try:
    from modules import init_model_registry
    init_model_registry()
except Exception as e:
    print(f"初始化失败: {e}")
    # 使用原有系统继续
```

### 问题3：兼容性问题

**症状**: 原有代码无法工作

**检查**:
```python
# 确保兼容性函数可用
from modules import (
    GET_VALID_OCR,
    GET_VALID_TRANSLATORS,
    GET_VALID_TEXTDETECTORS,
    GET_VALID_INPAINTERS,
)

# 测试调用
print(GET_VALID_OCR())  # 应返回模型列表
```

## 最佳实践

1. **启动顺序**
   - 先加载配置（config）
   - 再初始化模型注册表（modules）
   - 最后启动UI

2. **错误处理**
   - 初始化失败时不应阻止应用启动
   - 提供降级方案（使用原有系统）

3. **性能优化**
   - 模型注册表初始化只执行一次
   - 延迟加载自定义模型（按需）

4. **调试技巧**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   
   # 查看详细的迁移日志
   from modules import init_model_registry
   init_model_registry()
   ```
