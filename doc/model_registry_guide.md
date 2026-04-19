# 模型管理解耦系统使用说明

## 概述

本系统实现了模型依赖的解耦，允许用户自主选择、录入和管理模型，而无需修改代码。

## 核心组件

### 1. ModelRegistry (模型注册表)

位于 `modules/model_registry.py`

功能：
- 统一管理所有模型定义（与实现解耦）
- 支持动态添加/删除模型
- 支持从配置文件加载模型
- 提供统一的模型查询接口

### 2. ModelConfigManager (模型配置管理器)

位于 `modules/model_config_manager.py`

功能：
- 提供图形化界面管理模型
- 支持模型参数的编辑
- 支持导入/导出模型配置
- 与原有配置系统兼容

### 3. 新的配置面板

位于 `ui/new_model_panels.py`

功能：
- 替换原有的配置面板
- 集成新的模型管理器
- 保持与原有代码的兼容性

## 使用方法

### 方式一：使用新的模型管理器（推荐）

1. **在应用启动时初始化：**

```python
from modules import migrate_to_new_registry

# 启动时调用一次，将原有模型迁移到新系统
migrate_to_new_registry()
```

2. **在配置面板中使用：**

```python
from ui.new_model_panels import (
    NewTextDetectConfigPanel as TextDetectConfigPanel,
    NewOCRConfigPanel as OCRConfigPanel,
    NewInpaintConfigPanel as InpaintConfigPanel,
    NewTranslatorConfigPanel as TranslatorConfigPanel,
)
```

### 方式二：使用工厂函数

```python
from ui.new_model_panels import create_config_panels

# 创建配置面板类
TextDetectConfigPanel, OCRConfigPanel, InpaintConfigPanel, TranslatorConfigPanel = \
    create_config_panels(use_new_system=True)
```

### 方式三：混合使用

可以部分模块使用新系统，部分保持原有实现：

```python
from modules import model_registry, ModelType, ModelDefinition, ModelParameter

# 注册一个新的OCR模型（无需修改代码）
definition = ModelDefinition(
    key="my_custom_ocr",
    name="我的自定义OCR",
    model_type=ModelType.OCR,
    provider=ModelProvider.CUSTOM,
    description="这是一个自定义OCR模型",
    parameters=[
        ModelParameter(
            name="api_key",
            display_name="API密钥",
            param_type="line_editor",
            default_value="",
            editable=True,
            description="输入你的API密钥"
        ),
        ModelParameter(
            name="device",
            display_name="运行设备",
            param_type="selector",
            default_value="cpu",
            options=["cpu", "cuda", "mps"],
            description="选择运行设备"
        ),
    ],
    implementation_class="my_module.MyOCRClass",  # 可选：指定实现类
)

model_registry.register_model(definition)
```

## 用户自定义模型

### 通过UI添加模型

1. 打开配置面板
2. 点击"管理模型"按钮
3. 点击"添加模型"
4. 填写模型信息：
   - 模型Key：唯一标识（如 my_custom_model）
   - 模型名称：显示名称
   - 模型类型：OCR/文本检测/修复/翻译
   - 提供方：本地/API/自定义
   - 参数定义：添加模型需要的参数

### 通过JSON导入模型

1. 准备一个JSON文件，格式如下：

```json
{
  "key": "my_custom_model",
  "name": "My Custom Model",
  "model_type": "ocr",
  "provider": "custom",
  "description": "自定义模型描述",
  "parameters": [
    {
      "name": "api_key",
      "display_name": "API Key",
      "param_type": "line_editor",
      "default_value": "",
      "editable": true,
      "description": "API密钥",
      "data_type": "str"
    },
    {
      "name": "device",
      "display_name": "Device",
      "param_type": "selector",
      "default_value": "cpu",
      "options": ["cpu", "cuda", "mps"],
      "editable": false,
      "description": "运行设备",
      "data_type": "str"
    }
  ],
  "implementation_class": "",
  "enabled": true
}
```

2. 在模型管理器中点击"导入模型"
3. 选择JSON文件

### 手动添加模型文件

将JSON文件放入 `config/custom_models/` 目录，系统会自动加载。

## 模型参数类型

支持以下参数类型：

| 类型 | 说明 | 示例 |
|------|------|------|
| `selector` | 下拉选择 | device选择cpu/cuda |
| `line_editor` | 单行文本输入 | api_key输入 |
| `checkbox` | 复选框 | 启用/禁用选项 |
| `editor` | 多行文本输入 | 提示词模板 |

## 与原有系统的兼容性

### 向后兼容

- 所有原有API保持不变
- 原有配置文件可以继续使用
- 原有模型自动迁移到新系统

### 数据迁移

调用 `migrate_to_new_registry()` 会自动：
1. 扫描原有注册表中的所有模型
2. 提取模型参数定义
3. 注册到新系统中
4. 保持原有功能不变

## 高级用法

### 动态修改模型

```python
from modules import model_registry, ModelType

# 获取模型定义
definition = model_registry.get_model_definition(ModelType.OCR, "mit48px")

# 修改参数
for param in definition.parameters:
    if param.name == "device":
        param.default_value = "cuda"

# 重新注册
model_registry.register_model(definition)
```

### 创建模型模板

```python
# 导出模型模板供用户参考
model_registry.export_model_template(
    ModelType.OCR,
    "ocr_model_template.json"
)
```

### 批量导入模型

```python
import json
from pathlib import Path

models_dir = Path("models_configs")
for model_file in models_dir.glob("*.json"):
    with open(model_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    definition = ModelDefinition.from_dict(data)
    model_registry.register_model(definition)
```

## 注意事项

1. **模型Key唯一性**：每个模型的key必须唯一，不能重复
2. **实现类路径**：如果指定了implementation_class，需要确保类可以被正确导入
3. **参数类型**：selector类型必须提供options列表
4. **自定义模型**：用户自定义模型存储在 `config/custom_models/` 目录

## 故障排除

### 模型不显示

1. 检查模型是否启用（enabled=True）
2. 检查模型类型是否正确
3. 查看日志输出是否有错误信息

### 参数不生效

1. 检查参数名是否正确
2. 检查参数类型是否与值匹配
3. 确认参数已正确保存到配置

### 导入失败

1. 检查JSON格式是否正确
2. 检查必填字段是否完整
3. 检查model_type和provider是否为有效值
