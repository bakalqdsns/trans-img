#!/usr/bin/env python3
"""
BallonsTranslator 启动脚本示例
展示如何正确初始化和使用模型注册表解耦系统
"""

import sys
import os
from pathlib import Path

# 设置项目根目录
def setup_project_path():
    """设置项目路径"""
    project_root = Path(__file__).parent.parent.absolute()
    sys.path.insert(0, str(project_root))
    return project_root

# 初始化模型注册表
def init_model_system():
    """
    初始化模型系统
    
    方式一：自动初始化（推荐）
    导入 modules 包时会自动调用 init_model_registry()
    """
    print("正在初始化模型注册表...")
    
    from modules import (
        init_model_registry,
        GET_VALID_OCR,
        GET_VALID_TRANSLATORS,
        GET_VALID_TEXTDETECTORS,
        GET_VALID_INPAINTERS,
    )
    
    # 可选：显式调用初始化（如果禁用了自动初始化）
    # init_model_registry()
    
    # 验证初始化结果
    print("\n模型注册表初始化完成!")
    print("-" * 60)
    print(f"文本检测器: {len(GET_VALID_TEXTDETECTORS())} 个")
    print(f"OCR模型: {len(GET_VALID_OCR())} 个")
    print(f"修复器: {len(GET_VALID_INPAINTERS())} 个")
    print(f"翻译器: {len(GET_VALID_TRANSLATORS())} 个")
    print("-" * 60)

# 列出所有模型
def list_all_models():
    """列出所有可用的模型"""
    from modules import model_registry, ModelType, ModelProvider
    
    print("\n" + "=" * 60)
    print("详细模型列表")
    print("=" * 60)
    
    for model_type in ModelType:
        definitions = model_registry.get_model_definitions(model_type)
        if not definitions:
            continue
            
        print(f"\n【{model_type.value.upper()}】")
        
        # 按提供方分组
        local_models = []
        api_models = []
        custom_models = []
        
        for key, definition in definitions.items():
            if not definition.enabled:
                continue
                
            info = f"  - {definition.name} ({key})"
            if definition.parameters:
                info += f" [{len(definition.parameters)}个参数]"
            
            if definition.provider == ModelProvider.LOCAL:
                local_models.append(info)
            elif definition.provider == ModelProvider.API:
                api_models.append(info)
            elif definition.provider == ModelProvider.CUSTOM:
                custom_models.append(info)
        
        if local_models:
            print("  📦 内置模型:")
            for m in local_models:
                print(m)
        
        if api_models:
            print("  🌐 API服务:")
            for m in api_models:
                print(m)
        
        if custom_models:
            print("  🔧 自定义模型:")
            for m in custom_models:
                print(m)

# 添加自定义模型示例
def example_add_custom_model():
    """添加自定义模型示例"""
    from modules import (
        model_registry,
        ModelDefinition,
        ModelParameter,
        ModelType,
        ModelProvider,
    )
    
    print("\n" + "=" * 60)
    print("添加自定义模型示例")
    print("=" * 60)
    
    # 定义自定义OCR模型
    definition = ModelDefinition(
        key="example_custom_ocr",
        name="示例自定义OCR",
        model_type=ModelType.OCR,
        provider=ModelProvider.CUSTOM,
        description="这是一个示例自定义OCR模型",
        parameters=[
            ModelParameter(
                name="api_url",
                display_name="API地址",
                param_type="line_editor",
                default_value="http://localhost:8080/ocr",
                editable=True,
                description="OCR服务的API地址",
            ),
            ModelParameter(
                name="api_key",
                display_name="API密钥",
                param_type="line_editor",
                default_value="",
                editable=True,
                description="API认证密钥",
            ),
            ModelParameter(
                name="language",
                display_name="识别语言",
                param_type="selector",
                default_value="auto",
                options=["auto", "zh", "en", "ja", "ko"],
                editable=True,
                description="OCR识别的目标语言",
            ),
        ],
        enabled=True,
    )
    
    # 注册模型
    model_registry.register_model(definition)
    print(f"✓ 已添加自定义模型: {definition.name}")
    
    # 验证
    exists = model_registry.model_exists(ModelType.OCR, "example_custom_ocr")
    print(f"✓ 验证模型存在: {exists}")

# 导出模型模板
def example_export_template():
    """导出模型模板示例"""
    from modules import export_model_template, ModelType
    
    print("\n" + "=" * 60)
    print("导出模型模板")
    print("=" * 60)
    
    output_dir = Path(__file__).parent.parent / "config" / "custom_models"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 导出翻译器模板
    template_path = output_dir / "template_translator.json"
    export_model_template(ModelType.TRANSLATOR, str(template_path))
    print(f"✓ 已导出翻译器模板: {template_path}")
    
    # 导出OCR模板
    template_path = output_dir / "template_ocr.json"
    export_model_template(ModelType.OCR, str(template_path))
    print(f"✓ 已导出OCR模板: {template_path}")

# 主函数
def main():
    """主函数"""
    print("=" * 60)
    print("BallonsTranslator 模型注册表启动示例")
    print("=" * 60)
    
    # 1. 设置项目路径
    project_root = setup_project_path()
    print(f"\n项目根目录: {project_root}")
    
    # 2. 初始化模型系统
    init_model_system()
    
    # 3. 列出所有模型
    list_all_models()
    
    # 4. 添加自定义模型示例
    example_add_custom_model()
    
    # 5. 再次列出模型（验证添加成功）
    print("\n" + "=" * 60)
    print("添加自定义模型后的列表")
    print("=" * 60)
    from modules import GET_VALID_OCR
    print(f"OCR模型: {GET_VALID_OCR()}")
    
    # 6. 导出模板
    example_export_template()
    
    print("\n" + "=" * 60)
    print("启动示例完成!")
    print("=" * 60)
    print("\n提示:")
    print("  - 模型注册表已自动初始化")
    print("  - 自定义模型已保存到 config/custom_models/")
    print("  - 可以使用这些模型进行OCR/翻译等操作")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
