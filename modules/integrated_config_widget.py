# Integrated Model Config Widget
# 集成模型配置组件 - 将新的ModelManagerWidget与原有系统整合

"""
功能：
1. 提供统一的模型选择和配置界面
2. 支持动态模型录入
3. 与原有ModuleConfigParseWidget兼容
4. 支持模型参数的实时编辑和保存
"""

from typing import Dict, List, Optional, Any, Callable

from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QDialog, QMessageBox, QScrollArea, QFormLayout,
    QLineEdit, QCheckBox, QPlainTextEdit, QFileDialog, QGridLayout,
    QGroupBox, QSplitter, QTabWidget
)
from qtpy.QtCore import Qt, Signal

from .model_registry import ModelType, ModelProvider, model_registry, ModelDefinition
from .model_adapter import model_adapter, get_model_params
from .model_config_manager import (
    ModelManagerWidget, ModelManagerDialog, ModelDefinitionEditorDialog,
    ParameterEditorWidget
)
from utils.logger import logger as LOGGER


class IntegratedModelConfigWidget(QWidget):
    """
    集成模型配置组件
    
    替代原有的ModuleConfigParseWidget，提供：
    - 模型选择下拉框
    - 动态参数配置界面
    - 模型管理按钮（添加/编辑/删除自定义模型）
    """
    
    module_changed = Signal(str)  # model_key
    paramwidget_edited = Signal(str, dict)  # param_key, param_content
    
    def __init__(self, 
                 model_type: ModelType,
                 module_name: str,
                 scroll_widget: QWidget = None,
                 parent=None):
        super().__init__(parent)
        
        self.model_type = model_type
        self.module_name = module_name
        self.scroll_widget = scroll_widget
        self.current_model_key: Optional[str] = None
        self.param_widgets: Dict[str, ParameterEditorWidget] = {}
        
        self._setup_ui()
        self._refresh_model_list()
    
    def _setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 模型选择区域
        select_group = QGroupBox(f"{self.module_name} 模型选择")
        select_layout = QHBoxLayout(select_group)
        
        select_layout.addWidget(QLabel("选择模型:"))
        
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(200)
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        select_layout.addWidget(self.model_combo)
        
        # 管理按钮
        self.manage_btn = QPushButton("管理模型...")
        self.manage_btn.setToolTip("添加、编辑或删除自定义模型")
        self.manage_btn.clicked.connect(self._open_model_manager)
        select_layout.addWidget(self.manage_btn)
        
        select_layout.addStretch()
        layout.addWidget(select_group)
        
        # 参数配置区域
        param_group = QGroupBox("模型参数")
        param_layout = QVBoxLayout(param_group)
        
        self.param_scroll = QScrollArea()
        self.param_scroll.setWidgetResizable(True)
        self.param_scroll.setFrameShape(QScrollArea.NoFrame)
        
        self.param_container = QWidget()
        self.param_form_layout = QFormLayout(self.param_container)
        self.param_form_layout.setContentsMargins(10, 10, 10, 10)
        self.param_form_layout.setSpacing(10)
        
        self.param_scroll.setWidget(self.param_container)
        param_layout.addWidget(self.param_scroll)
        
        layout.addWidget(param_group)
        layout.addStretch()
    
    def _refresh_model_list(self):
        """刷新模型列表"""
        self.model_combo.clear()
        
        definitions = model_registry.get_model_definitions(self.model_type)
        
        # 按提供方分组
        local_models = []
        api_models = []
        custom_models = []
        
        for key, definition in definitions.items():
            if not definition.enabled:
                continue
            
            item_text = f"{definition.name} ({key})"
            if definition.provider == ModelProvider.LOCAL:
                local_models.append((item_text, key))
            elif definition.provider == ModelProvider.API:
                api_models.append((item_text, key))
            elif definition.provider == ModelProvider.CUSTOM:
                custom_models.append((item_text, key))
        
        # 添加分组
        if local_models:
            self.model_combo.addItem("--- 本地模型 ---")
            for text, key in local_models:
                self.model_combo.addItem(text, key)
        
        if api_models:
            self.model_combo.addItem("--- API服务 ---")
            for text, key in api_models:
                self.model_combo.addItem(text, key)
        
        if custom_models:
            self.model_combo.addItem("--- 自定义模型 ---")
            for text, key in custom_models:
                self.model_combo.addItem(text, key)
    
    def _on_model_changed(self, text: str):
        """模型选择改变时的处理"""
        # 跳过分隔符
        if text.startswith("---"):
            return
        
        model_key = self.model_combo.currentData()
        if not model_key:
            return
        
        self.current_model_key = model_key
        
        # 清除旧参数
        self._clear_parameters()
        
        # 加载新参数
        definition = model_registry.get_model_definition(self.model_type, model_key)
        if definition:
            for param in definition.parameters:
                widget = ParameterEditorWidget(param)
                widget.value_changed.connect(self._on_param_value_changed)
                self.param_widgets[param.name] = widget
                self.param_form_layout.addRow(param.display_name + ":", widget)
        
        self.module_changed.emit(model_key)
    
    def _clear_parameters(self):
        """清除参数控件"""
        self.param_widgets.clear()
        while self.param_form_layout.rowCount() > 0:
            self.param_form_layout.removeRow(0)
    
    def _on_param_value_changed(self, name: str, value: Any):
        """参数值改变时的处理"""
        content_dict = {'content': value}
        self.paramwidget_edited.emit(name, content_dict)
    
    def _open_model_manager(self):
        """打开模型管理器"""
        dialog = ModelManagerDialog(self.model_type, self)
        dialog.model_added.connect(self._refresh_model_list)
        dialog.exec()
    
    # 公共接口 - 与原有代码兼容
    
    def setModule(self, model_key: str):
        """设置当前模型"""
        # 查找模型对应的索引
        for i in range(self.model_combo.count()):
            if self.model_combo.itemData(i) == model_key:
                self.model_combo.setCurrentIndex(i)
                return
    
    def get_current_model(self) -> Optional[str]:
        """获取当前选中的模型key"""
        return self.current_model_key
    
    def get_parameter_values(self) -> Dict[str, Any]:
        """获取所有参数值"""
        values = {}
        for name, widget in self.param_widgets.items():
            values[name] = widget.get_value()
        return values
    
    def set_parameter_values(self, values: Dict[str, Any]):
        """设置参数值"""
        for name, value in values.items():
            if name in self.param_widgets:
                self.param_widgets[name].set_value(value)
    
    def addModulesParamWidgets(self, module_dict: Dict):
        """
        兼容原有接口 - 添加模块参数控件
        
        Args:
            module_dict: {model_key: params_dict}
        """
        # 这个接口在新架构中不需要实际处理
        # 参数由ModelRegistry动态管理
        pass


class IntegratedTextDetectConfigWidget(IntegratedModelConfigWidget):
    """集成文本检测器配置组件"""
    
    detector_changed = Signal(str)
    
    def __init__(self, module_name: str, scroll_widget: QWidget = None, parent=None):
        super().__init__(ModelType.TEXT_DETECTOR, module_name, scroll_widget, parent)
        self.detector_changed = self.module_changed
        self.setDetector = self.setModule


class IntegratedOCRConfigWidget(IntegratedModelConfigWidget):
    """集成OCR配置组件"""
    
    ocr_changed = Signal(str)
    
    def __init__(self, module_name: str, scroll_widget: QWidget = None, parent=None):
        super().__init__(ModelType.OCR, module_name, scroll_widget, parent)
        self.ocr_changed = self.module_changed
        self.setOCR = self.setModule


class IntegratedInpaintConfigWidget(IntegratedModelConfigWidget):
    """集成修复器配置组件"""
    
    inpainter_changed = Signal(str)
    
    def __init__(self, module_name: str, scroll_widget: QWidget = None, parent=None):
        super().__init__(ModelType.INPAINTER, module_name, scroll_widget, parent)
        self.inpainter_changed = self.module_changed
        self.setInpainter = self.setModule


class IntegratedTranslatorConfigWidget(IntegratedModelConfigWidget):
    """集成翻译器配置组件"""
    
    translator_changed = Signal(str)
    
    def __init__(self, module_name: str, scroll_widget: QWidget = None, parent=None):
        super().__init__(ModelType.TRANSLATOR, module_name, scroll_widget, parent)
        self.translator_changed = self.module_changed
        self.setTranslator = self.setModule


# 兼容性别名 - 与原有代码兼容
TextDetectConfigPanel = IntegratedTextDetectConfigWidget
OCRConfigPanel = IntegratedOCRConfigWidget
InpaintConfigPanel = IntegratedInpaintConfigWidget
TranslatorConfigPanel = IntegratedTranslatorConfigWidget
