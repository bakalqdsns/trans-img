#!/usr/bin/env python3
"""
模型管理解耦系统演示脚本

运行方式:
    python demo_model_registry.py

功能：
1. 展示模型注册表的使用
2. 演示如何动态添加模型
3. 展示模型配置的导入导出
"""

import sys
import json
import importlib.util
from pathlib import Path

# 直接加载 model_registry 模块，避免导入整个 modules 包
spec = importlib.util.spec_from_file_location("model_registry", 
    str(Path(__file__).parent / "modules" / "model_registry.py"))
model_registry_module = importlib.util.module_from_spec(spec)
sys.modules["model_registry"] = model_registry_module
spec.loader.exec_module(model_registry_module)

ModelRegistry = model_registry_module.ModelRegistry
ModelDefinition = model_registry_module.ModelDefinition
ModelParameter = model_registry_module.ModelParameter
ModelType = model_registry_module.ModelType
ModelProvider = model_registry_module.ModelProvider
model_registry = model_registry_module.model_registry


def demo_basic_usage():
    """演示基本用法"""
    print("=" * 60)
    print("演示1: 基本用法")
    print("=" * 60)
    
    # 获取所有OCR模型
    ocr_models = model_registry.get_model_keys(ModelType.OCR)
    print(f"\n当前OCR模型数量: {len(ocr_models)}")
    print(f"OCR模型列表: {ocr_models}")
    
    # 获取所有文本检测器
    detector_models = model_registry.get_model_keys(ModelType.TEXT_DETECTOR)
    print(f"\n当前文本检测器数量: {len(detector_models)}")
    
    # 获取所有翻译器
    translator_models = model_registry.get_model_keys(ModelType.TRANSLATOR)
    print(f"\n当前翻译器数量: {len(translator_models)}")
    
    # 获取所有修复器
    inpainter_models = model_registry.get_model_keys(ModelType.INPAINTER)
    print(f"\n当前修复器数量: {len(inpainter_models)}")


def demo_add_custom_model():
    """演示添加自定义模型"""
    print("\n" + "=" * 60)
    print("演示2: 添加自定义模型")
    print("=" * 60)
    
    # 定义一个新的OCR模型
    definition = ModelDefinition(
        key="demo_custom_ocr",
        name="演示自定义OCR",
        model_type=ModelType.OCR,
        provider=ModelProvider.CUSTOM,
        description="这是一个演示用的自定义OCR模型",
        parameters=[
            ModelParameter(
                name="api_endpoint",
                display_name="API端点",
                param_type="line_editor",
                default_value="https://api.example.com/ocr",
                editable=True,
                description="OCR服务的API端点地址"
            ),
            ModelParameter(
                name="api_key",
                display_name="API密钥",
                param_type="line_editor",
                default_value="",
                editable=True,
                description="访问API所需的密钥"
            ),
            ModelParameter(
                name="recognition_mode",
                display_name="识别模式",
                param_type="selector",
                default_value="accurate",
                options=["fast", "accurate", "balanced"],
                editable=False,
                description="选择识别速度和精度的平衡"
            ),
            ModelParameter(
                name="use_gpu",
                display_name="使用GPU",
                param_type="checkbox",
                default_value=True,
                editable=False,
                description="是否使用GPU加速"
            ),
        ],
        implementation_class="",  # 纯配置，无实现
        enabled=True
    )
    
    # 注册模型
    success = model_registry.register_model(definition)
    print(f"\n注册模型结果: {'成功' if success else '失败'}")
    
    # 验证模型已注册
    if model_registry.model_exists(ModelType.OCR, "demo_custom_ocr"):
        print("✓ 模型已成功注册到系统")
        
        # 获取模型定义
        registered_def = model_registry.get_model_definition(ModelType.OCR, "demo_custom_ocr")
        print(f"\n模型名称: {registered_def.name}")
        print(f"模型描述: {registered_def.description}")
        print(f"参数数量: {len(registered_def.parameters)}")
        
        print("\n参数列表:")
        for param in registered_def.parameters:
            print(f"  - {param.display_name} ({param.name}): {param.param_type}")
    
    return definition


def demo_export_import():
    """演示导出导入功能"""
    print("\n" + "=" * 60)
    print("演示3: 导出和导入模型配置")
    print("=" * 60)
    
    # 获取一个模型定义
    definition = model_registry.get_model_definition(ModelType.OCR, "demo_custom_ocr")
    
    if definition:
        # 导出为JSON
        json_data = definition.to_dict()
        print("\n导出的JSON配置:")
        print(json.dumps(json_data, ensure_ascii=False, indent=2))
        
        # 保存到文件
        output_file = Path("demo_model_export.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        print(f"\n✓ 配置已保存到: {output_file}")
        
        # 从JSON恢复
        with open(output_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        loaded_definition = ModelDefinition.from_dict(loaded_data)
        print(f"\n✓ 从JSON恢复模型: {loaded_definition.name}")
        
        # 清理
        output_file.unlink()
        print(f"✓ 清理临时文件")


def demo_model_query():
    """演示模型查询功能"""
    print("\n" + "=" * 60)
    print("演示4: 模型查询功能")
    print("=" * 60)
    
    # 获取所有模型定义
    all_definitions = model_registry.get_all_definitions()
    
    print("\n所有模型概览:")
    for model_type, definitions in all_definitions.items():
        print(f"\n{model_type.value.upper()}:")
        for key, definition in definitions.items():
            provider_icon = "🤖" if definition.provider == ModelProvider.LOCAL else "☁️" if definition.provider == ModelProvider.API else "👤"
            enabled_icon = "✓" if definition.enabled else "✗"
            print(f"  [{enabled_icon}] {provider_icon} {key}: {definition.name}")


def demo_remove_model():
    """演示删除模型"""
    print("\n" + "=" * 60)
    print("演示5: 删除模型")
    print("=" * 60)
    
    # 删除演示模型
    if model_registry.model_exists(ModelType.OCR, "demo_custom_ocr"):
        success = model_registry.unregister_model(ModelType.OCR, "demo_custom_ocr")
        print(f"\n删除模型结果: {'成功' if success else '失败'}")
        
        if not model_registry.model_exists(ModelType.OCR, "demo_custom_ocr"):
            print("✓ 模型已成功从系统移除")
    else:
        print("模型不存在或已被删除")


def demo_template_export():
    """演示模板导出"""
    print("\n" + "=" * 60)
    print("演示6: 导出模型模板")
    print("=" * 60)
    
    template_file = Path("demo_model_template.json")
    model_registry.export_model_template(ModelType.TRANSLATOR, str(template_file))
    
    if template_file.exists():
        print(f"\n✓ 模板已导出到: {template_file}")
        
        with open(template_file, 'r', encoding='utf-8') as f:
            template = json.load(f)
        
        print(f"\n模板内容预览:")
        print(f"  - Key: {template['key']}")
        print(f"  - 类型: {template['model_type']}")
        print(f"  - 参数数量: {len(template['parameters'])}")
        
        # 清理
        template_file.unlink()
        print(f"\n✓ 清理临时文件")


def print_summary():
    """打印总结"""
    print("\n" + "=" * 60)
    print("总结")
    print("=" * 60)
    
    summary = """
模型管理解耦系统提供了以下核心功能:

1. **模型定义与实现解耦**
   - 模型配置独立于代码
   - 支持动态添加/删除模型
   - 无需修改代码即可添加新模型

2. **用户自主录入**
   - 通过UI界面添加模型
   - 通过JSON文件导入模型
   - 支持参数化配置

3. **统一管理接口**
   - 统一的模型注册表
   - 统一的查询接口
   - 统一的配置管理

4. **向后兼容**
   - 原有API保持不变
   - 自动迁移原有模型
   - 渐进式采用新系统

使用场景:
- 添加第三方API模型
- 自定义本地模型配置
- 模型参数的灵活调整
- 模型配置的版本管理
"""
    print(summary)


def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "模型管理解耦系统演示" + " " * 23 + "║")
    print("╚" + "=" * 58 + "╝")
    
    try:
        # 运行演示
        demo_basic_usage()
        demo_add_custom_model()
        demo_export_import()
        demo_model_query()
        demo_remove_model()
        demo_template_export()
        print_summary()
        
        print("\n✓ 所有演示完成!")
        
    except Exception as e:
        print(f"\n✗ 演示出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
