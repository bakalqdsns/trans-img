"""
新的模型配置面板集成示例

这个文件展示了如何将新的模型管理器集成到现有的配置面板中
可以替换原有的 ModuleConfigParseWidget 使用方式
"""

from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QCheckBox
)
from qtpy.QtCore import Qt, Signal

# 导入新的模型管理器
from modules import (
    ModelManagerWidget, 
    ModelManagerDialog,
    ModelType,
    model_registry,
    migrate_to_new_registry,
)

# 导入原有组件以保持兼容性
from ui.module_parse_widgets import (
    ParamWidget, 
    ModuleConfigParseWidget,
    TranslatorConfigPanel as OldTranslatorConfigPanel,
    InpaintConfigPanel as OldInpaintConfigPanel,
    TextDetectConfigPanel as OldTextDetectConfigPanel,
    OCRConfigPanel as OldOCRConfigPanel,
)


class NewTranslatorConfigPanel(QWidget):
    """
    新的翻译器配置面板 - 使用模型管理器
    """
    
    module_changed = Signal(str)
    paramwidget_edited = Signal(str, dict)
    translator_changed = Signal(str)
    
    def __init__(self, module_name: str, scrollWidget: QWidget = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        layout = QVBoxLayout(self)
        
        # 使用新的模型管理器
        self.model_manager = ModelManagerWidget(ModelType.TRANSLATOR)
        self.model_manager.model_changed.connect(self._on_model_changed)
        layout.addWidget(self.model_manager)
        
        # 源语言和目标语言选择
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("源语言:"))
        self.source_combo = QComboBox()
        lang_layout.addWidget(self.source_combo)
        lang_layout.addWidget(QLabel("目标语言:"))
        self.target_combo = QComboBox()
        lang_layout.addWidget(self.target_combo)
        lang_layout.addStretch()
        
        layout.addLayout(lang_layout)
        layout.addStretch()
        
        self.translator_changed = self.model_manager.model_changed
    
    def _on_model_changed(self, model_key: str):
        """模型改变时更新语言列表"""
        self.module_changed.emit(model_key)
        
        # 这里可以根据模型定义更新语言选项
        # 实际实现需要根据具体模型获取支持的语言列表
    
    def finishSetTranslator(self, translator):
        """设置翻译器（兼容原有接口）"""
        self.model_manager.set_current_model(translator.name)
        
        # 设置语言
        self.source_combo.clear()
        self.target_combo.clear()
        self.source_combo.addItems(translator.supported_src_list)
        self.target_combo.addItems(translator.supported_tgt_list)
        self.source_combo.setCurrentText(translator.lang_source)
        self.target_combo.setCurrentText(translator.lang_target)
    
    def addModulesParamWidgets(self, module_dict: dict):
        """兼容原有接口"""
        # 新的实现不需要这个，模型定义已经包含参数信息
        pass
    
    def setModule(self, module: str):
        """兼容原有接口"""
        self.model_manager.set_current_model(module)


class NewOCRConfigPanel(QWidget):
    """
    新的OCR配置面板 - 使用模型管理器
    """
    
    module_changed = Signal(str)
    paramwidget_edited = Signal(str, dict)
    ocr_changed = Signal(str)
    
    def __init__(self, module_name: str, scrollWidget: QWidget = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        layout = QVBoxLayout(self)
        
        # 使用新的模型管理器
        self.model_manager = ModelManagerWidget(ModelType.OCR)
        self.model_manager.model_changed.connect(self._on_model_changed)
        layout.addWidget(self.model_manager)
        
        # 额外选项
        self.restore_empty_checker = QCheckBox("删除并恢复OCR返回空字符串的区域")
        layout.addWidget(self.restore_empty_checker)
        
        self.font_detect_checker = QCheckBox("字体检测")
        layout.addWidget(self.font_detect_checker)
        
        layout.addStretch()
        
        self.ocr_changed = self.model_manager.model_changed
        self.setOCR = self.model_manager.set_current_model
    
    def _on_model_changed(self, model_key: str):
        """模型改变"""
        self.module_changed.emit(model_key)


class NewTextDetectConfigPanel(QWidget):
    """
    新的文本检测配置面板 - 使用模型管理器
    """
    
    module_changed = Signal(str)
    paramwidget_edited = Signal(str, dict)
    detector_changed = Signal(str)
    
    def __init__(self, module_name: str, scrollWidget: QWidget = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        layout = QVBoxLayout(self)
        
        # 使用新的模型管理器
        self.model_manager = ModelManagerWidget(ModelType.TEXT_DETECTOR)
        self.model_manager.model_changed.connect(self._on_model_changed)
        layout.addWidget(self.model_manager)
        
        # 额外选项
        self.keep_existing_checker = QCheckBox("保留现有文本行")
        layout.addWidget(self.keep_existing_checker)
        
        layout.addStretch()
        
        self.detector_changed = self.model_manager.model_changed
        self.setDetector = self.model_manager.set_current_model
    
    def _on_model_changed(self, model_key: str):
        """模型改变"""
        self.module_changed.emit(model_key)


class NewInpaintConfigPanel(QWidget):
    """
    新的修复配置面板 - 使用模型管理器
    """
    
    module_changed = Signal(str)
    paramwidget_edited = Signal(str, dict)
    inpainter_changed = Signal(str)
    
    def __init__(self, module_name: str, scrollWidget: QWidget = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        layout = QVBoxLayout(self)
        
        # 使用新的模型管理器
        self.model_manager = ModelManagerWidget(ModelType.INPAINTER)
        self.model_manager.model_changed.connect(self._on_model_changed)
        layout.addWidget(self.model_manager)
        
        # 额外选项
        self.need_inpaint_checker = QCheckBox("让程序决定是否需要使用选定的修复方法")
        layout.addWidget(self.need_inpaint_checker)
        
        layout.addStretch()
        
        self.inpainter_changed = self.model_manager.model_changed
        self.setInpainter = self.model_manager.set_current_model
    
    def _on_model_changed(self, model_key: str):
        """模型改变"""
        self.module_changed.emit(model_key)


def create_config_panels(use_new_system: bool = False):
    """
    创建配置面板工厂函数
    
    Args:
        use_new_system: 是否使用新的模型管理系统
    
    Returns:
        tuple: (detect_panel, ocr_panel, inpaint_panel, translator_panel)
    """
    if use_new_system:
        # 确保已迁移
        migrate_to_new_registry()
        
        return (
            NewTextDetectConfigPanel,
            NewOCRConfigPanel,
            NewInpaintConfigPanel,
            NewTranslatorConfigPanel,
        )
    else:
        # 使用原有实现
        return (
            OldTextDetectConfigPanel,
            OldOCRConfigPanel,
            OldInpaintConfigPanel,
            OldTranslatorConfigPanel,
        )


# 使用示例：
"""
# 在应用启动时调用一次迁移
from modules import migrate_to_new_registry
migrate_to_new_registry()

# 在配置面板中使用新的模型管理器
# 修改 ui/configpanel.py 中的导入：

# 原有导入：
# from .module_parse_widgets import InpaintConfigPanel, TextDetectConfigPanel, TranslatorConfigPanel, OCRConfigPanel

# 新的导入方式：
from .new_model_panels import (
    NewTextDetectConfigPanel as TextDetectConfigPanel,
    NewOCRConfigPanel as OCRConfigPanel,
    NewInpaintConfigPanel as InpaintConfigPanel,
    NewTranslatorConfigPanel as TranslatorConfigPanel,
)

# 或者使用工厂函数：
TextDetectConfigPanel, OCRConfigPanel, InpaintConfigPanel, TranslatorConfigPanel = create_config_panels(use_new_system=True)
"""
