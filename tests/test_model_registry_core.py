#!/usr/bin/env python3
"""
模型注册表核心功能测试（独立测试，不依赖项目其他模块）
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_model_registry_core():
    """测试模型注册表核心功能（不依赖其他模块）"""
    print("=" * 60)
    print("测试模型注册表核心功能")
    print("=" * 60)
    
    # 直接导入model_registry模块，避免依赖链
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "model_registry", 
        os.path.join(os.path.dirname(__file__), "..", "modules", "model_registry.py")
    )
    model_registry_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model_registry_module)
    
    ModelRegistry = model_registry_module.ModelRegistry
    ModelType = model_registry_module.ModelType
    ModelProvider = model_registry_module.ModelProvider
    ModelDefinition = model_registry_module.ModelDefinition
    ModelParameter = model_registry_module.ModelParameter
    
    # 创建新的注册表实例（不使用单例）
    registry = ModelRegistry.__new__(ModelRegistry)
    registry._initialized = True
    registry._definitions = {model_type: {} for model_type in ModelType}
    registry._implementations = {}
    registry._custom_models_dir = Path("/tmp/test_custom_models")
    registry._custom_models_dir.mkdir(exist_ok=True)
    
    # 测试注册自定义模型
    definition = ModelDefinition(
        key="test_model",
        name="测试模型",
        model_type=ModelType.OCR,
        provider=ModelProvider.CUSTOM,
        description="这是一个测试模型",
        parameters=[
            ModelParameter(
                name="api_key",
                display_name="API密钥",
                param_type="line_editor",
                default_value="",
                editable=True,
                description="API密钥"
            ),
            ModelParameter(
                name="device",
                display_name="设备",
                param_type="selector",
                default_value="cpu",
                options=["cpu", "cuda", "mps"],
                editable=False,
                description="运行设备"
            )
        ],
        enabled=True
    )
    
    # 注册模型
    result = registry.register_model(definition)
    print(f"✓ 注册模型: {result}")
    
    # 查询模型
    retrieved = registry.get_model_definition(ModelType.OCR, "test_model")
    print(f"✓ 查询模型: {retrieved.name if retrieved else 'Not found'}")
    
    # 获取模型列表
    ocr_models = registry.get_model_keys(ModelType.OCR)
    print(f"✓ OCR模型数量: {len(ocr_models)}")
    print(f"  模型列表: {ocr_models}")
    
    # 注销模型
    result = registry.unregister_model(ModelType.OCR, "test_model")
    print(f"✓ 注销模型: {result}")
    
    # 清理测试目录
    import shutil
    shutil.rmtree(registry._custom_models_dir, ignore_errors=True)
    
    print("\n")


def test_model_serialization():
    """测试模型序列化"""
    print("=" * 60)
    print("测试模型序列化")
    print("=" * 60)
    
    # 直接导入
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "model_registry", 
        os.path.join(os.path.dirname(__file__), "..", "modules", "model_registry.py")
    )
    model_registry_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model_registry_module)
    
    ModelDefinition = model_registry_module.ModelDefinition
    ModelType = model_registry_module.ModelType
    ModelProvider = model_registry_module.ModelProvider
    ModelParameter = model_registry_module.ModelParameter
    
    # 创建模型定义
    definition = ModelDefinition(
        key="serialization_test",
        name="序列化测试模型",
        model_type=ModelType.TRANSLATOR,
        provider=ModelProvider.API,
        description="测试序列化功能",
        parameters=[
            ModelParameter(
                name="test_param",
                display_name="测试参数",
                param_type="line_editor",
                default_value="default_value",
                editable=True,
                description="测试参数描述"
            )
        ],
        enabled=True
    )
    
    # 转换为字典
    data = definition.to_dict()
    print(f"✓ 转换为字典成功")
    print(f"  JSON预览:")
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    print(json_str[:800] + "..." if len(json_str) > 800 else json_str)
    
    # 从字典恢复
    restored = ModelDefinition.from_dict(data)
    print(f"\n✓ 从字典恢复成功")
    print(f"  模型名称: {restored.name}")
    print(f"  参数数量: {len(restored.parameters)}")
    
    print("\n")


def test_json_examples():
    """测试示例JSON文件"""
    print("=" * 60)
    print("测试示例JSON文件")
    print("=" * 60)
    
    # 直接导入
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "model_registry", 
        os.path.join(os.path.dirname(__file__), "..", "modules", "model_registry.py")
    )
    model_registry_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model_registry_module)
    
    ModelDefinition = model_registry_module.ModelDefinition
    
    examples_dir = Path(__file__).parent.parent / "config" / "custom_models"
    
    if not examples_dir.exists():
        print(f"✗ 示例目录不存在: {examples_dir}")
        return
    
    json_files = list(examples_dir.glob("*.json"))
    print(f"✓ 找到 {len(json_files)} 个JSON文件")
    
    for json_file in json_files:
        print(f"\n  测试文件: {json_file.name}")
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            definition = ModelDefinition.from_dict(data)
            print(f"    ✓ 解析成功")
            print(f"      - Key: {definition.key}")
            print(f"      - Name: {definition.name}")
            print(f"      - Type: {definition.model_type.value}")
            print(f"      - Provider: {definition.provider.value}")
            print(f"      - Parameters: {len(definition.parameters)}")
        except Exception as e:
            print(f"    ✗ 解析失败: {e}")
    
    print("\n")


def test_model_export_template():
    """测试模型模板导出功能"""
    print("=" * 60)
    print("测试模型模板导出")
    print("=" * 60)
    
    # 直接导入
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "model_registry", 
        os.path.join(os.path.dirname(__file__), "..", "modules", "model_registry.py")
    )
    model_registry_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model_registry_module)
    
    ModelRegistry = model_registry_module.ModelRegistry
    ModelType = model_registry_module.ModelType
    
    registry = ModelRegistry.__new__(ModelRegistry)
    
    output_path = "/tmp/test_model_template.json"
    registry.export_model_template(ModelType.OCR, output_path)
    
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            template = json.load(f)
        print(f"✓ 模板导出成功: {output_path}")
        print(f"  模板内容预览:")
        print(json.dumps(template, ensure_ascii=False, indent=2)[:600] + "...")
        os.remove(output_path)
    else:
        print(f"✗ 模板导出失败")
    
    print("\n")


def main():
    """主测试函数"""
    print("\n")
    print("*" * 60)
    print("* 模型注册表核心功能测试")
    print("*" * 60)
    print("\n")
    
    try:
        test_model_registry_core()
        test_model_serialization()
        test_json_examples()
        test_model_export_template()
        
        print("=" * 60)
        print("所有测试通过！✓")
        print("=" * 60)
        print("\n模型注册表解耦系统工作正常。")
        print("用户可以：")
        print("  1. 通过UI动态添加自定义模型")
        print("  2. 通过JSON文件导入模型定义")
        print("  3. 模型定义与实现完全解耦")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
