# Model Configuration Manager
# 模型配置管理器 - 处理模型配置的UI和持久化

"""
功能：
1. 模型配置的动态录入界面
2. 模型配置的验证和保存
3. 与原有配置系统的兼容
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import json
import os
from pathlib import Path

from qtpy.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QCheckBox, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFileDialog, QGroupBox, QFormLayout,
    QScrollArea, QWidget, QGridLayout, QPlainTextEdit, QDialogButtonBox,
    QTabWidget, QSplitter, QMenu, QAction, QInputDialog
)
from qtpy.QtCore import Qt, Signal
from qtpy.QtGui import QKeyEvent

from .model_registry import (
    ModelRegistry, ModelDefinition, ModelParameter, 
    ModelType, ModelProvider, model_registry
)
from utils.logger import logger as LOGGER


class ParameterEditorWidget(QWidget):
    """参数编辑器组件"""
    
    value_changed = Signal(str, Any)  # param_name, value
    
    def __init__(self, parameter: ModelParameter, parent=None):
        super().__init__(parent)
        self.parameter = parameter
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        param_type = self.parameter.param_type
        
        if param_type == "selector":
            self.editor = QComboBox()
            self.editor.addItems(self.parameter.options or [])
            self.editor.setCurrentText(str(self.parameter.default_value))
            self.editor.setEditable(self.parameter.editable)
            self.editor.currentTextChanged.connect(self._on_value_changed)
            
        elif param_type == "checkbox":
            self.editor = QCheckBox()
            self.editor.setChecked(bool(self.parameter.default_value))
            self.editor.stateChanged.connect(self._on_value_changed)
            
        elif param_type == "editor":
            self.editor = QPlainTextEdit()
            self.editor.setPlainText(str(self.parameter.default_value or ""))
            self.editor.setMaximumHeight(100)
            self.editor.textChanged.connect(self._on_value_changed)
            
        else:  # line_editor or default
            self.editor = QLineEdit()
            self.editor.setText(str(self.parameter.default_value or ""))
            self.editor.textChanged.connect(self._on_value_changed)
        
        # 添加描述提示
        if self.parameter.description:
            self.editor.setToolTip(self.parameter.description)
        
        layout.addWidget(self.editor)
    
    def _on_value_changed(self):
        self.value_changed.emit(self.parameter.name, self.get_value())
    
    def get_value(self) -> Any:
        """获取当前值"""
        param_type = self.parameter.param_type
        
        if param_type == "selector":
            return self.editor.currentText()
        elif param_type == "checkbox":
            return self.editor.isChecked()
        elif param_type == "editor":
            return self.editor.toPlainText()
        else:
            return self.editor.text()
    
    def set_value(self, value: Any):
        """设置值"""
        param_type = self.parameter.param_type
        
        if param_type == "selector":
            self.editor.setCurrentText(str(value))
        elif param_type == "checkbox":
            self.editor.setChecked(bool(value))
        elif param_type == "editor":
            self.editor.setPlainText(str(value))
        else:
            self.editor.setText(str(value))


class ModelDefinitionEditorDialog(QDialog):
    """模型定义编辑器对话框"""
    
    model_saved = Signal(ModelDefinition)
    
    def __init__(self, model_type: ModelType = None, existing_model: ModelDefinition = None, parent=None):
        super().__init__(parent)
        self.model_type = model_type
        self.existing_model = existing_model
        self.parameters: List[ModelParameter] = []
        self.param_widgets: Dict[str, QWidget] = {}
        
        self.setWindowTitle("模型定义编辑器" if existing_model else "添加新模型")
        self.setMinimumSize(700, 600)
        
        self._setup_ui()
        
        if existing_model:
            self._load_existing_model()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 基本信息组
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout(basic_group)
        
        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("模型唯一标识（如：my_custom_ocr）")
        basic_layout.addRow("模型Key*:", self.key_edit)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("模型显示名称（如：我的自定义OCR）")
        basic_layout.addRow("模型名称*:", self.name_edit)
        
        self.type_combo = QComboBox()
        for mt in ModelType:
            self.type_combo.addItem(mt.value, mt)
        if self.model_type:
            self.type_combo.setCurrentText(self.model_type.value)
        basic_layout.addRow("模型类型*:", self.type_combo)
        
        self.provider_combo = QComboBox()
        for p in ModelProvider:
            self.provider_combo.addItem(p.value, p)
        basic_layout.addRow("提供方*:", self.provider_combo)
        
        self.desc_edit = QPlainTextEdit()
        self.desc_edit.setMaximumHeight(80)
        self.desc_edit.setPlaceholderText("模型描述...")
        basic_layout.addRow("描述:", self.desc_edit)
        
        self.impl_class_edit = QLineEdit()
        self.impl_class_edit.setPlaceholderText("实现类路径（如：modules.ocr.my_ocr.MyOCR）")
        basic_layout.addRow("实现类:", self.impl_class_edit)
        
        self.enabled_check = QCheckBox("启用此模型")
        self.enabled_check.setChecked(True)
        basic_layout.addRow("", self.enabled_check)
        
        layout.addWidget(basic_group)
        
        # 参数管理组
        param_group = QGroupBox("参数定义")
        param_layout = QVBoxLayout(param_group)
        
        # 参数表格
        self.param_table = QTableWidget()
        self.param_table.setColumnCount(6)
        self.param_table.setHorizontalHeaderLabels([
            "参数名", "显示名", "类型", "默认值", "选项", "描述"
        ])
        self.param_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.param_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.param_table.customContextMenuRequested.connect(self._show_param_context_menu)
        param_layout.addWidget(self.param_table)
        
        # 添加参数按钮
        btn_layout = QHBoxLayout()
        add_param_btn = QPushButton("+ 添加参数")
        add_param_btn.clicked.connect(self._add_parameter)
        btn_layout.addWidget(add_param_btn)
        
        import_btn = QPushButton("导入JSON")
        import_btn.clicked.connect(self._import_from_json)
        btn_layout.addWidget(import_btn)
        
        export_btn = QPushButton("导出JSON")
        export_btn.clicked.connect(self._export_to_json)
        btn_layout.addWidget(export_btn)
        
        btn_layout.addStretch()
        param_layout.addLayout(btn_layout)
        
        layout.addWidget(param_group)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._on_save)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _load_existing_model(self):
        """加载现有模型数据"""
        model = self.existing_model
        self.key_edit.setText(model.key)
        self.key_edit.setEnabled(False)  # 编辑时不能修改key
        self.name_edit.setText(model.name)
        self.type_combo.setCurrentText(model.model_type.value)
        self.provider_combo.setCurrentText(model.provider.value)
        self.desc_edit.setPlainText(model.description)
        self.impl_class_edit.setText(model.implementation_class)
        self.enabled_check.setChecked(model.enabled)
        
        # 加载参数
        for param in model.parameters:
            self._add_parameter_to_table(param)
    
    def _add_parameter(self):
        """添加新参数"""
        dialog = ParameterDefinitionDialog(self)
        if dialog.exec() == QDialog.Accepted:
            param = dialog.get_parameter()
            self._add_parameter_to_table(param)
    
    def _add_parameter_to_table(self, param: ModelParameter):
        """添加参数到表格"""
        row = self.param_table.rowCount()
        self.param_table.insertRow(row)
        
        self.param_table.setItem(row, 0, QTableWidgetItem(param.name))
        self.param_table.setItem(row, 1, QTableWidgetItem(param.display_name))
        self.param_table.setItem(row, 2, QTableWidgetItem(param.param_type))
        self.param_table.setItem(row, 3, QTableWidgetItem(str(param.default_value)))
        self.param_table.setItem(row, 4, QTableWidgetItem(",".join(param.options) if param.options else ""))
        self.param_table.setItem(row, 5, QTableWidgetItem(param.description))
        
        # 存储参数对象
        self.param_table.item(row, 0).setData(Qt.UserRole, param)
    
    def _show_param_context_menu(self, position):
        """显示参数右键菜单"""
        menu = QMenu()
        
        edit_action = QAction("编辑", self)
        edit_action.triggered.connect(self._edit_selected_param)
        menu.addAction(edit_action)
        
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(self._delete_selected_param)
        menu.addAction(delete_action)
        
        menu.exec(self.param_table.viewport().mapToGlobal(position))
    
    def _edit_selected_param(self):
        """编辑选中的参数"""
        row = self.param_table.currentRow()
        if row < 0:
            return
        
        param = self.param_table.item(row, 0).data(Qt.UserRole)
        dialog = ParameterDefinitionDialog(self, param)
        
        if dialog.exec() == QDialog.Accepted:
            new_param = dialog.get_parameter()
            # 更新表格
            self.param_table.setItem(row, 0, QTableWidgetItem(new_param.name))
            self.param_table.setItem(row, 1, QTableWidgetItem(new_param.display_name))
            self.param_table.setItem(row, 2, QTableWidgetItem(new_param.param_type))
            self.param_table.setItem(row, 3, QTableWidgetItem(str(new_param.default_value)))
            self.param_table.setItem(row, 4, QTableWidgetItem(
                ",".join(new_param.options) if new_param.options else ""))
            self.param_table.setItem(row, 5, QTableWidgetItem(new_param.description))
            self.param_table.item(row, 0).setData(Qt.UserRole, new_param)
    
    def _delete_selected_param(self):
        """删除选中的参数"""
        row = self.param_table.currentRow()
        if row >= 0:
            self.param_table.removeRow(row)
    
    def _import_from_json(self):
        """从JSON导入"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择JSON文件", "", "JSON files (*.json)"
        )
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            definition = ModelDefinition.from_dict(data)
            self.existing_model = definition
            self._load_existing_model()
            
            QMessageBox.information(self, "成功", "模型定义已导入")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")
    
    def _export_to_json(self):
        """导出为JSON"""
        definition = self._build_definition()
        if not definition:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存JSON文件", f"{definition.key}.json", "JSON files (*.json)"
        )
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(definition.to_dict(), f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "成功", f"已保存到: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def _build_definition(self) -> Optional[ModelDefinition]:
        """构建模型定义"""
        key = self.key_edit.text().strip()
        name = self.name_edit.text().strip()
        
        if not key or not name:
            QMessageBox.warning(self, "验证失败", "模型Key和名称不能为空")
            return None
        
        # 收集参数
        parameters = []
        for row in range(self.param_table.rowCount()):
            param = self.param_table.item(row, 0).data(Qt.UserRole)
            parameters.append(param)
        
        return ModelDefinition(
            key=key,
            name=name,
            model_type=self.type_combo.currentData(),
            provider=self.provider_combo.currentData(),
            description=self.desc_edit.toPlainText(),
            parameters=parameters,
            implementation_class=self.impl_class_edit.text().strip(),
            enabled=self.enabled_check.isChecked()
        )
    
    def _on_save(self):
        """保存模型"""
        definition = self._build_definition()
        if not definition:
            return
        
        # 注册到系统
        model_registry.register_model(definition)
        
        self.model_saved.emit(definition)
        self.accept()


class ParameterDefinitionDialog(QDialog):
    """参数定义对话框"""
    
    def __init__(self, parent=None, existing_param: ModelParameter = None):
        super().__init__(parent)
        self.existing_param = existing_param
        self.setWindowTitle("编辑参数" if existing_param else "添加参数")
        self.setMinimumWidth(400)
        
        self._setup_ui()
        
        if existing_param:
            self._load_existing()
    
    def _setup_ui(self):
        layout = QFormLayout(self)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("参数名（如：api_key）")
        layout.addRow("参数名*:", self.name_edit)
        
        self.display_name_edit = QLineEdit()
        self.display_name_edit.setPlaceholderText("显示名称（如：API密钥）")
        layout.addRow("显示名*:", self.display_name_edit)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["selector", "line_editor", "checkbox", "editor"])
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        layout.addRow("参数类型*:", self.type_combo)
        
        self.options_edit = QLineEdit()
        self.options_edit.setPlaceholderText("选项1,选项2,选项3（selector类型用）")
        layout.addRow("选项:", self.options_edit)
        
        self.default_edit = QLineEdit()
        self.default_edit.setPlaceholderText("默认值")
        layout.addRow("默认值:", self.default_edit)
        
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("参数描述")
        layout.addRow("描述:", self.desc_edit)
        
        self.editable_check = QCheckBox("可编辑")
        layout.addRow("", self.editable_check)
        
        # 按钮
        btn_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._on_save)
        btn_box.rejected.connect(self.reject)
        layout.addRow(btn_box)
    
    def _on_type_changed(self, text):
        """参数类型改变"""
        self.options_edit.setEnabled(text == "selector")
    
    def _load_existing(self):
        """加载现有参数"""
        p = self.existing_param
        self.name_edit.setText(p.name)
        self.display_name_edit.setText(p.display_name)
        self.type_combo.setCurrentText(p.param_type)
        self.options_edit.setText(",".join(p.options) if p.options else "")
        self.default_edit.setText(str(p.default_value or ""))
        self.desc_edit.setText(p.description)
        self.editable_check.setChecked(p.editable)
    
    def _on_save(self):
        """保存参数"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "验证失败", "参数名不能为空")
            return
        self.accept()
    
    def get_parameter(self) -> ModelParameter:
        """获取参数定义"""
        param_type = self.type_combo.currentText()
        default_value = self.default_edit.text()
        
        # 根据类型转换默认值
        if param_type == "checkbox":
            default_value = default_value.lower() in ("true", "1", "yes", "on")
        
        options = None
        if param_type == "selector" and self.options_edit.text():
            options = [o.strip() for o in self.options_edit.text().split(",")]
        
        return ModelParameter(
            name=self.name_edit.text().strip(),
            display_name=self.display_name_edit.text().strip() or self.name_edit.text().strip(),
            param_type=param_type,
            default_value=default_value,
            options=options,
            editable=self.editable_check.isChecked(),
            description=self.desc_edit.text()
        )


class ModelManagerWidget(QWidget):
    """
    模型管理器组件 - 集成到配置面板
    """
    
    model_changed = Signal(str)  # model_key
    
    def __init__(self, model_type: ModelType, parent=None):
        super().__init__(parent)
        self.model_type = model_type
        self.current_model_key: Optional[str] = None
        self.param_widgets: Dict[str, ParameterEditorWidget] = {}
        
        self._setup_ui()
        self._refresh_model_list()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 模型选择行
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("模型:"))
        
        self.model_combo = QComboBox()
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        select_layout.addWidget(self.model_combo, 1)
        
        # 管理按钮
        self.manage_btn = QPushButton("管理模型")
        self.manage_btn.clicked.connect(self._open_model_manager)
        select_layout.addWidget(self.manage_btn)
        
        layout.addLayout(select_layout)
        
        # 参数区域
        self.param_scroll = QScrollArea()
        self.param_scroll.setWidgetResizable(True)
        self.param_scroll.setFrameShape(QScrollArea.NoFrame)
        
        self.param_container = QWidget()
        self.param_layout = QFormLayout(self.param_container)
        self.param_layout.setContentsMargins(0, 10, 0, 0)
        
        self.param_scroll.setWidget(self.param_container)
        layout.addWidget(self.param_scroll)
    
    def _refresh_model_list(self):
        """刷新模型列表"""
        self.model_combo.clear()
        
        definitions = model_registry.get_model_definitions(self.model_type)
        for key, definition in definitions.items():
            if definition.enabled:
                self.model_combo.addItem(definition.name, key)
    
    def _on_model_changed(self, text):
        """模型选择改变"""
        if not text:
            return
        
        model_key = self.model_combo.currentData()
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
                self.param_layout.addRow(param.display_name + ":", widget)
        
        self.model_changed.emit(model_key)
    
    def _clear_parameters(self):
        """清除参数控件"""
        self.param_widgets.clear()
        while self.param_layout.rowCount() > 0:
            self.param_layout.removeRow(0)
    
    def _on_param_value_changed(self, name: str, value: Any):
        """参数值改变"""
        # 可以在这里实时保存配置
        pass
    
    def _open_model_manager(self):
        """打开模型管理器"""
        dialog = ModelManagerDialog(self.model_type, self)
        dialog.model_added.connect(self._refresh_model_list)
        dialog.exec()
    
    def set_current_model(self, model_key: str):
        """设置当前模型"""
        index = self.model_combo.findData(model_key)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
    
    def get_current_model(self) -> Optional[str]:
        """获取当前选中的模型"""
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


class ModelManagerDialog(QDialog):
    """模型管理对话框"""
    
    model_added = Signal()
    
    def __init__(self, model_type: ModelType = None, parent=None):
        super().__init__(parent)
        self.model_type = model_type
        self.setWindowTitle("模型管理器")
        self.setMinimumSize(800, 600)
        
        self._setup_ui()
        self._refresh_model_list()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 类型筛选
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("模型类型:"))
        
        self.type_filter = QComboBox()
        self.type_filter.addItem("全部", None)
        for mt in ModelType:
            self.type_filter.addItem(mt.value, mt)
        if self.model_type:
            self.type_filter.setCurrentText(self.model_type.value)
        self.type_filter.currentIndexChanged.connect(self._refresh_model_list)
        filter_layout.addWidget(self.type_filter)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # 模型列表
        self.model_table = QTableWidget()
        self.model_table.setColumnCount(5)
        self.model_table.setHorizontalHeaderLabels([
            "Key", "名称", "类型", "提供方", "启用"
        ])
        self.model_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.model_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.model_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.model_table.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.model_table)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("+ 添加模型")
        add_btn.clicked.connect(self._add_model)
        btn_layout.addWidget(add_btn)
        
        import_btn = QPushButton("导入模型")
        import_btn.clicked.connect(self._import_model)
        btn_layout.addWidget(import_btn)
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._refresh_model_list)
        btn_layout.addWidget(refresh_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def _refresh_model_list(self):
        """刷新模型列表"""
        self.model_table.setRowCount(0)
        
        filter_type = self.type_filter.currentData()
        all_definitions = model_registry.get_all_definitions()
        
        for model_type, definitions in all_definitions.items():
            if filter_type and model_type != filter_type:
                continue
            
            for key, definition in definitions.items():
                row = self.model_table.rowCount()
                self.model_table.insertRow(row)
                
                self.model_table.setItem(row, 0, QTableWidgetItem(definition.key))
                self.model_table.setItem(row, 1, QTableWidgetItem(definition.name))
                self.model_table.setItem(row, 2, QTableWidgetItem(definition.model_type.value))
                self.model_table.setItem(row, 3, QTableWidgetItem(definition.provider.value))
                
                enabled_item = QTableWidgetItem("是" if definition.enabled else "否")
                self.model_table.setItem(row, 4, enabled_item)
                
                # 存储定义对象
                self.model_table.item(row, 0).setData(Qt.UserRole, definition)
    
    def _show_context_menu(self, position):
        """显示右键菜单"""
        row = self.model_table.currentRow()
        if row < 0:
            return
        
        menu = QMenu()
        
        edit_action = QAction("编辑", self)
        edit_action.triggered.connect(self._edit_model)
        menu.addAction(edit_action)
        
        toggle_action = QAction("启用/禁用", self)
        toggle_action.triggered.connect(self._toggle_model)
        menu.addAction(toggle_action)
        
        export_action = QAction("导出JSON", self)
        export_action.triggered.connect(self._export_model)
        menu.addAction(export_action)
        
        menu.addSeparator()
        
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(self._delete_model)
        menu.addAction(delete_action)
        
        menu.exec(self.model_table.viewport().mapToGlobal(position))
    
    def _add_model(self):
        """添加新模型"""
        dialog = ModelDefinitionEditorDialog(
            model_type=self.type_filter.currentData(),
            parent=self
        )
        dialog.model_saved.connect(lambda: self.model_added.emit())
        if dialog.exec() == QDialog.Accepted:
            self._refresh_model_list()
            self.model_added.emit()
    
    def _edit_model(self):
        """编辑模型"""
        row = self.model_table.currentRow()
        if row < 0:
            return
        
        definition = self.model_table.item(row, 0).data(Qt.UserRole)
        dialog = ModelDefinitionEditorDialog(
            existing_model=definition,
            parent=self
        )
        if dialog.exec() == QDialog.Accepted:
            self._refresh_model_list()
            self.model_added.emit()
    
    def _toggle_model(self):
        """启用/禁用模型"""
        row = self.model_table.currentRow()
        if row < 0:
            return
        
        definition = self.model_table.item(row, 0).data(Qt.UserRole)
        definition.enabled = not definition.enabled
        
        # 重新注册
        model_registry.register_model(definition)
        self._refresh_model_list()
    
    def _export_model(self):
        """导出模型"""
        row = self.model_table.currentRow()
        if row < 0:
            return
        
        definition = self.model_table.item(row, 0).data(Qt.UserRole)
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出模型", f"{definition.key}.json", "JSON files (*.json)"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(definition.to_dict(), f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "成功", f"已导出到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def _delete_model(self):
        """删除模型"""
        row = self.model_table.currentRow()
        if row < 0:
            return
        
        definition = self.model_table.item(row, 0).data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除模型 '{definition.name}' 吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            model_registry.unregister_model(definition.model_type, definition.key)
            self._refresh_model_list()
            self.model_added.emit()
    
    def _import_model(self):
        """导入模型"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择模型文件", "", "JSON files (*.json)"
        )
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            definition = ModelDefinition.from_dict(data)
            definition.provider = ModelProvider.CUSTOM  # 标记为自定义
            
            model_registry.register_model(definition)
            self._refresh_model_list()
            self.model_added.emit()
            
            QMessageBox.information(self, "成功", f"模型 '{definition.name}' 已导入")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")
