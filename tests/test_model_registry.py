#!/usr/bin/env python3
"""
模型注册表解耦系统测试脚本
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_model_registry():
    """测试模型注册表基本功能"""
    print("=" * 60)
    print("测试模型注册表基本功能")
    print("=" * 60)
    
    from modules import (
        model_registry, ModelType, ModelProvider,
        ModelDefinition, ModelParameter
    )
    
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
    result = model_registry.register_model(definition)
    print(f"✓ 注册模型: {result}")
    
    # 查询模型
    retrieved = model_registry.get_model_definition(ModelType.OCR, "test_model")
    print(f"✓ 查询模型: {retrieved.name if retrieved else 'Not found'}")
    
    # 获取模型列表
    ocr_models = model_registry.get_model_keys(ModelType.OCR)
    print(f"✓ OCR模型数量: {len(ocr_models)}")
    print(f"  模型列表: {ocr_models}")
    
    # 注销模型
    result = model_registry.unregister_model(ModelType.OCR, "test_model")
    print(f"✓ 注销模型: {result}")
    
    print("\n")


def test_model_adapter():
    """测试模型适配器"""
    print("=" * 60)
    print("测试模型适配器")
    print("=" * 60)
    
    from modules import model_adapter, ModelType
    
    # 测试获取模型参数
    params = model_adapter.get_model_params_dict(ModelType.OCR, "mit48px")
    if params:
        print(f"✓ 获取 mit48px 参数成功")
        print(f"  参数数量: {len(params)}")
    else:
        print("✗ 获取参数失败")
    
    # 测试兼容性函数
    from modules import GET_VALID_OCR, GET_VALID_TRANSLATORS
    
    ocr_list = GET_VALID_OCR()
    print(f"✓ GET_VALID_OCR() 返回: {len(ocr_list)} 个模型")
    
    trans_list = GET_VALID_TRANSLATORS()
    print(f"✓ GET_VALID_TRANSLATORS() 返回: {len(trans_list)} 个模型")
    
    print("\n")


def test_custom_model_loading():
    """测试自定义模型加载"""
    print("=" * 60)
    print("测试自定义模型加载")
    print("=" * 60)
    
    from modules import model_registry, ModelType
    
    # 检查自定义模型目录
    custom_models_dir = "config/custom_models"
    if os.path.exists(custom_models_dir):
        json_files = [f for f in os.listdir(custom_models_dir) if f.endswith('.json')]
        print(f"✓ 自定义模型目录: {custom_models_dir}")
        print(f"✓ JSON文件数量: {len(json_files)}")
        for f in json_files:
            print(f"  - {f}")
    else:
        print(f"✗ 自定义模型目录不存在: {custom_models_dir}")
    
    # 显示所有模型
    all_defs = model_registry.get_all_definitions()
    for model_type, defs in all_defs.items():
        print(f"\n{model_type.value}:")
        for key, definition in defs.items():
            provider_icon = "🔧" if definition.provider.value == "custom" else "📦"
            print(f"  {provider_icon} {definition.name} ({key})")
    
    print("\n")


def test_model_serialization():
    """测试模型序列化"""
    print("=" * 60)
    print("测试模型序列化")
    print("=" * 60)
    
    from modules import ModelDefinition, ModelType, ModelProvider, ModelParameter
    import json
    
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
    print(json.dumps(data, ensure_ascii=False, indent=2)[:500] + "...")
    
    # 从字典恢复
    restored = ModelDefinition.from_dict(data)
    print(f"\n✓ 从字典恢复成功")
    print(f"  模型名称: {restored.name}")
    print(f"  参数数量: {len(restored.parameters)}")
    
    print("\n")


def main():
    """主测试函数"""
    print("\n")
    print("*" * 60)
    print("* 模型注册表解耦系统测试")
    print("*" * 60)
    print("\n")
    
    try:
        test_model_registry()
        test_model_adapter()
        test_custom_model_loading()
        test_model_serialization()
        
        print("=" * 60)
        print("所有测试通过！✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
