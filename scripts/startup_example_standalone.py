#!/usr/bin/env python3
"""
BallonsTranslator 模型注册表启动示例（独立版本）
不依赖项目的其他模块，仅展示核心功能
"""

import sys
import os
import json
from pathlib import Path

# 设置项目根目录
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

# 直接导入model_registry，避免依赖链
def import_model_registry():
    """导入模型注册表模块"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "model_registry",
        project_root / "modules" / "model_registry.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    """主函数"""
    print("=" * 60)
    print("BallonsTranslator 模型注册表启动示例（独立版本）")
    print("=" * 60)
    
    # 导入模型注册表
    print("\n1. 导入模型注册表核心模块...")
    mr = import_model_registry()
    print("   ✓ 导入成功")
    
    # 创建注册表实例
    print("\n2. 创建模型注册表实例...")
    registry = mr.ModelRegistry.__new__(mr.ModelRegistry)
    registry._initialized = True
    registry._definitions = {mt: {} for mt in mr.ModelType}
    registry._implementations = {}
    registry._custom_models_dir = project_root / "config" / "custom_models"
    print(f"   ✓ 注册表创建成功")
    print(f"   ✓ 自定义模型目录: {registry._custom_models_dir}")
    
    # 加载自定义模型
    print("\n3. 加载自定义模型...")
    if registry._custom_models_dir.exists():
        json_files = list(registry._custom_models_dir.glob("*.json"))
        print(f"   找到 {len(json_files)} 个JSON文件")
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                definition = mr.ModelDefinition.from_dict(data)
                registry._definitions[definition.model_type][definition.key] = definition
                print(f"   ✓ 加载: {definition.name} ({definition.key})")
            except Exception as e:
                print(f"   ✗ 失败: {json_file.name} - {e}")
    
    # 显示所有模型
    print("\n4. 模型列表:")
    print("-" * 60)
    
    for model_type in mr.ModelType:
        definitions = registry._definitions[model_type]
        if not definitions:
            continue
        
        print(f"\n【{model_type.value.upper()}】")
        for key, definition in definitions.items():
            provider_icon = {
                mr.ModelProvider.LOCAL: "📦",
                mr.ModelProvider.API: "🌐",
                mr.ModelProvider.CUSTOM: "🔧",
            }.get(definition.provider, "❓")
            
            print(f"  {provider_icon} {definition.name}")
            print(f"     Key: {key}")
            print(f"     参数: {len(definition.parameters)} 个")
            if definition.parameters:
                for param in definition.parameters:
                    print(f"       - {param.display_name}: {param.param_type}")
    
    # 添加示例模型
    print("\n5. 添加示例模型...")
    example_model = mr.ModelDefinition(
        key="example_model",
        name="示例模型",
        model_type=mr.ModelType.OCR,
        provider=mr.ModelProvider.CUSTOM,
        description="通过代码动态添加的示例模型",
        parameters=[
            mr.ModelParameter(
                name="api_url",
                display_name="API地址",
                param_type="line_editor",
                default_value="http://localhost:8080",
                editable=True,
                description="服务地址",
            ),
        ],
        enabled=True,
    )
    
    registry.register_model(example_model)
    print(f"   ✓ 已添加: {example_model.name}")
    
    # 验证
    print("\n6. 验证模型:")
    exists = registry.model_exists(mr.ModelType.OCR, "example_model")
    print(f"   ✓ 模型存在: {exists}")
    
    ocr_models = registry.get_model_keys(mr.ModelType.OCR)
    print(f"   ✓ OCR模型总数: {len(ocr_models)}")
    
    # 导出模板
    print("\n7. 导出模型模板...")
    template_path = project_root / "config" / "custom_models" / "template_exported.json"
    registry.export_model_template(mr.ModelType.TRANSLATOR, str(template_path))
    if template_path.exists():
        print(f"   ✓ 模板已导出: {template_path}")
        # 读取并显示内容
        with open(template_path, 'r', encoding='utf-8') as f:
            template = json.load(f)
        print(f"   ✓ 模板内容预览:")
        preview = json.dumps(template, ensure_ascii=False, indent=2)[:400]
        print(preview + "...")
        # 清理
        template_path.unlink()
    
    print("\n" + "=" * 60)
    print("启动示例完成!")
    print("=" * 60)
    print("\n总结:")
    print("  ✓ 模型注册表核心功能工作正常")
    print("  ✓ 可以加载自定义模型JSON文件")
    print("  ✓ 可以通过代码动态添加模型")
    print("  ✓ 可以导出模型模板")
    print("\n在实际应用中，导入 modules 包时会自动完成以上初始化。")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
