# 模型注册表快速参考

## 一句话说明

**导入 `modules` 包即自动完成初始化**，原有代码无需任何修改即可获得新功能。

## 快速开始

### 1. 基础使用（原有代码）

```python
from modules import GET_VALID_OCR, GET_VALID_TRANSLATORS

# 直接使用，自动初始化
ocr_models = GET_VALID_OCR()
translator_models = GET_VALID_TRANSLATORS()
```

### 2. 添加自定义模型（代码方式）

```python
from modules import model_registry, ModelDefinition, ModelType, ModelParameter

definition = ModelDefinition(
    key="my_model",
    name="我的模型",
    model_type=ModelType.OCR,
    parameters=[
        ModelParameter(
            name="api_key",
            display_name="API密钥",
            param_type="line_editor",
            default_value="",
        )
    ],
)
model_registry.register_model(definition)
```

### 3. 添加自定义模型（JSON方式）

创建文件 `config/custom_models/my_model.json`:

```json
{
  "key": "my_model",
  "name": "我的模型",
  "model_type": "ocr",
  "provider": "custom",
  "parameters": [
    {
      "name": "api_key",
      "display_name": "API密钥",
      "param_type": "line_editor",
      "default_value": ""
    }
  ]
}
```

重启应用即可自动加载。

## 常用API

### 获取模型列表

```python
from modules import (
    GET_VALID_TEXTDETECTORS,
    GET_VALID_OCR,
    GET_VALID_INPAINTERS,
    GET_VALID_TRANSLATORS,
)

detectors = GET_VALID_TEXTDETECTORS()
ocr_models = GET_VALID_OCR()
inpainters = GET_VALID_INPAINTERS()
translators = GET_VALID_TRANSLATORS()
```

### 模型注册表操作

```python
from modules import model_registry, ModelType

# 获取模型定义
definition = model_registry.get_model_definition(ModelType.OCR, "mit48px")

# 获取所有模型
all_ocr = model_registry.get_model_definitions(ModelType.OCR)

# 检查模型是否存在
exists = model_registry.model_exists(ModelType.OCR, "my_model")

# 注销模型
model_registry.unregister_model(ModelType.OCR, "my_model")
```

### UI组件

```python
from modules import IntegratedOCRConfigWidget

# 在配置面板中使用
widget = IntegratedOCRConfigWidget("OCR", scroll_widget=parent)
widget.module_changed.connect(on_model_changed)
```

## 参数类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `line_editor` | 单行文本输入 | API密钥、URL |
| `selector` | 下拉选择框 | 设备选择(cpu/cuda) |
| `checkbox` | 复选框 | 启用/禁用选项 |
| `editor` | 多行文本编辑器 | 系统提示词 |

## 文件位置

```
BallonsTranslator/
├── modules/
│   ├── model_registry.py          # 核心注册表
│   ├── model_adapter.py           # 适配器
│   ├── model_config_manager.py    # UI管理器
│   └── integrated_config_widget.py # 集成组件
├── config/custom_models/          # 自定义模型目录
│   └── *.json                     # 模型定义文件
└── docs/                          # 文档
    ├── MODEL_REGISTRY_GUIDE.md    # 完整指南
    ├── STARTUP_GUIDE.md           # 启动指南
    └── DECOUPLING_SUMMARY.md      # 解耦总结
```

## 故障排查

### 模型未显示

```python
from modules import model_registry, ModelType

# 检查模型是否存在
print(model_registry.model_exists(ModelType.OCR, "my_model"))

# 检查所有模型
print(model_registry.get_model_keys(ModelType.OCR))
```

### 初始化问题

```python
# 手动初始化
try:
    from modules import init_model_registry
    init_model_registry()
except Exception as e:
    print(f"初始化失败: {e}")
```

## 示例代码

### 完整示例

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

# 设置路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入（自动初始化）
from modules import (
    model_registry,
    ModelType,
    ModelDefinition,
    ModelParameter,
    GET_VALID_OCR,
)

# 1. 查看现有模型
print("OCR模型:", GET_VALID_OCR())

# 2. 添加自定义模型
definition = ModelDefinition(
    key="custom_api",
    name="自定义API",
    model_type=ModelType.OCR,
    parameters=[
        ModelParameter(
            name="url",
            display_name="API地址",
            param_type="line_editor",
            default_value="http://localhost:8080",
        ),
    ],
)
model_registry.register_model(definition)

# 3. 验证
print("添加后:", GET_VALID_OCR())
```

运行:
```bash
cd BallonsTranslator
python3 my_script.py
```

## 获取更多帮助

- 完整指南: `docs/MODEL_REGISTRY_GUIDE.md`
- 启动指南: `docs/STARTUP_GUIDE.md`
- 集成示例: `docs/model_integration_examples.py`
- 启动示例: `scripts/startup_example_standalone.py`
