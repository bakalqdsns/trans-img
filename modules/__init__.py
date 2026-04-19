"""
Modules package - 模型模块包

重构后的模型管理架构：
1. model_registry.py - 模型注册表，解耦模型定义与实现
2. model_config_manager.py - 模型配置管理UI
3. model_adapter.py - 适配器，桥接新旧架构
4. 原有模块保持兼容
"""

# 导入模型注册表（新架构）
from .model_registry import (
    ModelRegistry,
    ModelDefinition,
    ModelParameter,
    ModelType,
    ModelProvider,
    model_registry,
    register_model_definition,
)

# 导入模型适配器（新架构）
from .model_adapter import (
    ModelAdapter,
    model_adapter,
    migrate_all_modules,
    register_custom_model,
    export_model_template,
    get_model_params,
    # 兼容性函数
    GET_VALID_TEXTDETECTORS,
    GET_VALID_OCR,
    GET_VALID_INPAINTERS,
    GET_VALID_TRANSLATORS,
)

# 导入模型配置管理器（新架构）- 可选导入，支持无GUI环境
try:
    from .model_config_manager import (
        ModelManagerWidget,
        ModelManagerDialog,
        ModelDefinitionEditorDialog,
        ParameterEditorWidget,
    )
    from .integrated_config_widget import (
        IntegratedModelConfigWidget,
        IntegratedTextDetectConfigWidget,
        IntegratedOCRConfigWidget,
        IntegratedInpaintConfigWidget,
        IntegratedTranslatorConfigWidget,
        # 兼容性别名
        TextDetectConfigPanel,
        OCRConfigPanel,
        InpaintConfigPanel,
        TranslatorConfigPanel,
    )
    _has_gui = True
except ImportError as e:
    _has_gui = False
    ModelManagerWidget = None
    ModelManagerDialog = None
    ModelDefinitionEditorDialog = None
    ParameterEditorWidget = None
    IntegratedModelConfigWidget = None
    IntegratedTextDetectConfigWidget = None
    IntegratedOCRConfigWidget = None
    IntegratedInpaintConfigWidget = None
    IntegratedTranslatorConfigWidget = None
    TextDetectConfigPanel = None
    OCRConfigPanel = None
    InpaintConfigPanel = None
    TranslatorConfigPanel = None

# 保持向后兼容 - 原有导入
from .ocr import OCR, OCRBase
from .textdetector import TEXTDETECTORS, TextDetectorBase
from .translators import TRANSLATORS, BaseTranslator
from .inpaint import INPAINTERS, InpainterBase
from .base import (
    DEFAULT_DEVICE, 
    GPUINTENSIVE_SET, 
    LOGGER, 
    merge_config_module_params,
    init_module_registries, 
    init_textdetector_registries, 
    init_inpainter_registries, 
    init_ocr_registries, 
    init_translator_registries
)

# 模块类型到注册表的映射（兼容新旧架构）
MODULETYPE_TO_REGISTRIES = {
    'textdetector': TEXTDETECTORS,
    'ocr': OCR,
    'inpainter': INPAINTERS,
    'translator': TRANSLATORS
}

# 模块类型到ModelType的映射
MODULETYPE_TO_MODELTYPE = {
    'textdetector': ModelType.TEXT_DETECTOR,
    'ocr': ModelType.OCR,
    'inpainter': ModelType.INPAINTER,
    'translator': ModelType.TRANSLATOR,
}

# 延迟迁移：在所有子模块导入完成后调用
# 这确保了 migrate_all_modules() 能看到所有已注册的模型
try:
    migrate_all_modules()
except Exception as e:
    LOGGER.warning(f"模型注册表迁移失败: {e}")
