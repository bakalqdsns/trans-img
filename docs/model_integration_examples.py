# 模型解耦集成使用示例
"""
展示如何在实际应用中使用新的模型注册表系统
"""

# ============================================
# 示例1：在启动时初始化模型注册表
# ============================================

def example_init_registry():
    """初始化模型注册表 - 在应用启动时调用"""
    from modules import init_model_registry
    
    # 这将自动迁移所有原有模型到新的注册表
    init_model_registry()
    
    print("模型注册表初始化完成")


# ============================================
# 示例2：获取可用模型列表
# ============================================

def example_get_models():
    """获取可用模型列表"""
    from modules import (
        GET_VALID_TEXTDETECTORS,
        GET_VALID_OCR,
        GET_VALID_INPAINTERS,
        GET_VALID_TRANSLATORS
    )
    
    # 获取所有文本检测器
    detectors = GET_VALID_TEXTDETECTORS()
    print(f"可用文本检测器: {detectors}")
    
    # 获取所有OCR模型
    ocr_models = GET_VALID_OCR()
    print(f"可用OCR模型: {ocr_models}")
    
    # 获取所有修复器
    inpainters = GET_VALID_INPAINTERS()
    print(f"可用修复器: {inpainters}")
    
    # 获取所有翻译器
    translators = GET_VALID_TRANSLATORS()
    print(f"可用翻译器: {translators}")


# ============================================
# 示例3：动态添加自定义模型
# ============================================

def example_add_custom_model():
    """动态添加自定义模型"""
    from modules import (
        model_registry,
        ModelDefinition,
        ModelParameter,
        ModelType,
        ModelProvider
    )
    
    # 定义新的OCR模型
    definition = ModelDefinition(
        key="my_custom_ocr",
        name="我的自定义OCR",
        model_type=ModelType.OCR,
        provider=ModelProvider.CUSTOM,
        description="通过代码动态添加的自定义OCR模型",
        parameters=[
            ModelParameter(
                name="api_endpoint",
                display_name="API端点",
                param_type="line_editor",
                default_value="http://localhost:8080/ocr",
                editable=True,
                description="OCR服务的API地址"
            ),
            ModelParameter(
                name="language",
                display_name="识别语言",
                param_type="selector",
                default_value="auto",
                options=["auto", "zh", "en", "ja", "ko"],
                editable=True,
                description="识别语言"
            ),
        ],
        enabled=True
    )
    
    # 注册模型
    model_registry.register_model(definition)
    print(f"已添加自定义模型: {definition.name}")


# ============================================
# 示例4：从JSON文件导入模型
# ============================================

def example_import_from_json(json_file_path: str):
    """从JSON文件导入模型定义"""
    import json
    from modules import model_registry, ModelDefinition, ModelProvider
    
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 标记为自定义模型
    data['provider'] = ModelProvider.CUSTOM.value
    
    definition = ModelDefinition.from_dict(data)
    model_registry.register_model(definition)
    
    print(f"已导入模型: {definition.name}")


# ============================================
# 示例5：在UI中使用新的配置组件
# ============================================

def example_ui_integration():
    """在UI中使用集成配置组件"""
    from qtpy.QtWidgets import QApplication, QWidget, QVBoxLayout
    from modules import (
        IntegratedTextDetectConfigWidget,
        IntegratedOCRConfigWidget,
        IntegratedInpaintConfigWidget,
        IntegratedTranslatorConfigWidget
    )
    
    app = QApplication([])
    
    window = QWidget()
    layout = QVBoxLayout(window)
    
    # 添加文本检测器配置
    detect_config = IntegratedTextDetectConfigWidget(
        module_name="文本检测",
        scroll_widget=window
    )
    layout.addWidget(detect_config)
    
    # 添加OCR配置
    ocr_config = IntegratedOCRConfigWidget(
        module_name="OCR",
        scroll_widget=window
    )
    layout.addWidget(ocr_config)
    
    # 添加修复器配置
    inpaint_config = IntegratedInpaintConfigWidget(
        module_name="图像修复",
        scroll_widget=window
    )
    layout.addWidget(inpaint_config)
    
    # 添加翻译器配置
    translator_config = IntegratedTranslatorConfigWidget(
        module_name="翻译",
        scroll_widget=window
    )
    layout.addWidget(translator_config)
    
    window.show()
    app.exec()


# ============================================
# 示例6：获取和设置模型参数
# ============================================

def example_model_params():
    """获取和设置模型参数"""
    from modules import model_adapter, ModelType
    
    # 获取模型参数（兼容原有格式）
    params = model_adapter.get_model_params_dict(ModelType.OCR, "mit48px")
    print(f"mit48px 参数: {params}")
    
    # 获取当前参数值
    from modules import model_registry
    definition = model_registry.get_model_definition(ModelType.OCR, "mit48px")
    
    if definition:
        for param in definition.parameters:
            print(f"  {param.display_name}: {param.default_value}")


# ============================================
# 示例7：导出模型模板
# ============================================

def example_export_template():
    """导出模型模板"""
    from modules import export_model_template, ModelType
    
    # 导出OCR模型模板
    export_model_template(ModelType.OCR, "ocr_template.json")
    print("已导出OCR模型模板: ocr_template.json")
    
    # 导出翻译器模型模板
    export_model_template(ModelType.TRANSLATOR, "translator_template.json")
    print("已导出翻译器模型模板: translator_template.json")


# ============================================
# 示例8：模型管理对话框
# ============================================

def example_model_manager_dialog():
    """打开模型管理对话框"""
    from qtpy.QtWidgets import QApplication
    from modules import ModelManagerDialog, ModelType
    
    app = QApplication([])
    
    # 打开特定类型的模型管理器
    dialog = ModelManagerDialog(ModelType.OCR)
    dialog.exec()


# ============================================
# 主函数
# ============================================

if __name__ == "__main__":
    print("模型解耦集成使用示例")
    print("=" * 60)
    
    # 注意：以下示例需要在正确的环境中运行
    # 某些示例需要Qt环境
    
    # example_init_registry()
    # example_get_models()
    # example_add_custom_model()
    # example_model_params()
    # example_export_template()
    
    print("\n示例代码已准备就绪")
    print("请根据实际需求选择相应的示例函数运行")
