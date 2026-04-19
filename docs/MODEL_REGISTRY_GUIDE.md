# 模型解耦与动态录入系统使用说明

## 概述

本系统实现了模型依赖的完全解耦，支持用户自主选择、配置和录入新模型，无需修改源代码。

## 架构说明

### 核心组件

1. **model_registry.py** - 模型注册表
   - 统一管理所有模型定义
   - 支持模型定义的动态添加/删除
   - 模型定义与实现完全解耦

2. **model_adapter.py** - 模型适配器
   - 桥接新旧架构
   - 自动迁移原有模型
   - 提供兼容性接口

3. **model_config_manager.py** - 模型配置管理器
   - 提供UI界面管理模型
   - 支持模型定义的增删改查
   - 参数编辑器组件

4. **integrated_config_widget.py** - 集成配置组件
   - 与原有UI系统整合
   - 提供模型选择和参数配置界面

## 使用方法

### 1. 使用内置模型

系统启动时会自动将所有内置模型迁移到新的注册表，用户可以：
- 在配置面板中选择任意内置模型
- 修改模型参数
- 参数会自动保存到配置文件

### 2. 添加自定义模型

#### 方法一：通过UI添加

1. 打开应用，进入配置面板
2. 点击"管理模型..."按钮
3. 在模型管理器中点击"+ 添加模型"
4. 填写模型信息：
   - 模型Key：唯一标识（如：my_custom_model）
   - 模型名称：显示名称
   - 模型类型：textdetector/ocr/inpainter/translator
   - 提供方：local/api/custom
   - 描述：模型说明
5. 添加参数定义：
   - 点击"+ 添加参数"
   - 设置参数名、显示名、类型、默认值等
6. 点击"保存"

#### 方法二：通过JSON文件导入

1. 参考 `config/custom_models/example_*.json` 创建模型定义文件
2. 在模型管理器中点击"导入模型"
3. 选择JSON文件

#### 方法三：直接放置JSON文件

1. 将模型定义JSON文件放入 `config/custom_models/` 目录
2. 重启应用，系统会自动加载

### 3. 模型定义JSON格式

```json
{
  "key": "模型唯一标识",
  "name": "模型显示名称",
  "model_type": "模型类型(textdetector/ocr/inpainter/translator)",
  "provider": "提供方(local/api/custom)",
  "description": "模型描述",
  "parameters": [
    {
      "name": "参数名",
      "display_name": "显示名称",
      "param_type": "参数类型(selector/line_editor/checkbox/editor)",
      "default_value": "默认值",
      "options": ["选项1", "选项2"],
      "editable": true,
      "description": "参数描述",
      "data_type": "数据类型(str/int/float/bool)"
    }
  ],
  "implementation_class": "实现类路径(可选)",
  "enabled": true
}
```

### 4. 参数类型说明

- **selector**: 下拉选择框，需要提供options列表
- **line_editor**: 单行文本输入框
- **checkbox**: 复选框，值为true/false
- **editor**: 多行文本编辑器

### 5. 导出模型

1. 在模型管理器中右键点击模型
2. 选择"导出JSON"
3. 选择保存位置

## 开发者指南

### 为自定义模型添加实现

如果需要为自定义模型添加实际的实现代码：

1. 创建实现类，继承自相应的基类：
   - OCR: `OCRBase`
   - TextDetector: `TextDetectorBase`
   - Inpainter: `InpainterBase`
   - Translator: `BaseTranslator`

2. 在模型定义中指定 `implementation_class`：
   ```json
   "implementation_class": "modules.translators.my_translator.MyTranslator"
   ```

3. 系统会通过动态导入加载实现类

### 在代码中使用模型注册表

```python
from modules import model_registry, ModelType

# 获取所有OCR模型
ocr_models = model_registry.get_model_definitions(ModelType.OCR)

# 获取特定模型定义
definition = model_registry.get_model_definition(ModelType.OCR, "mit48px")

# 创建模型实例
instance = model_registry.create_model_instance(
    ModelType.OCR, 
    "mit48px",
    device="cuda"
)
```

## 示例

### 示例1：添加自定义翻译API

参考 `config/custom_models/example_custom_openai.json`

### 示例2：添加自定义OCR服务

参考 `config/custom_models/example_custom_ocr.json`

## 注意事项

1. 模型Key必须唯一，不能与现有模型重复
2. 自定义模型保存在 `config/custom_models/` 目录
3. 修改模型定义后需要重启应用才能生效
4. 建议导出备份自定义模型定义

## 迁移说明

对于原有代码的兼容性：
- 所有原有导入保持不变
- `GET_VALID_*` 函数仍然可用
- 原有配置会自动迁移到新系统
- 新系统完全向后兼容
