# Model Registry Decoupling System
# 模型注册表解耦系统

"""
设计目标：
1. 将模型定义与模型实现解耦
2. 支持动态模型录入（用户可自主添加新模型）
3. 统一的模型配置管理接口
4. 支持模型参数的动态配置
"""

from typing import Dict, List, Callable, Optional, Type, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import os
from pathlib import Path


class ModelType(Enum):
    """模型类型枚举"""
    TEXT_DETECTOR = "textdetector"
    OCR = "ocr"
    INPAINTER = "inpainter"
    TRANSLATOR = "translator"
    TEXT_TRANSLATOR = TRANSLATOR


class ModelProvider(Enum):
    """模型提供方枚举"""
    LOCAL = "local"           # 本地模型
    API = "api"               # API服务
    CUSTOM = "custom"         # 用户自定义


@dataclass
class ModelParameter:
    """模型参数定义"""
    name: str                           # 参数名
    display_name: str                   # 显示名称
    param_type: str                     # 参数类型: selector, line_editor, checkbox, editor
    default_value: Any                  # 默认值
    options: List[str] = None           # 选项列表（selector类型用）
    editable: bool = False              # 是否可编辑
    description: str = ""               # 参数描述
    data_type: type = str               # 数据类型


@dataclass
class ModelDefinition:
    """模型定义 - 与具体实现解耦"""
    key: str                            # 模型唯一标识
    name: str                           # 模型显示名称
    model_type: ModelType               # 模型类型
    provider: ModelProvider             # 提供方类型
    description: str = ""               # 模型描述
    parameters: List[ModelParameter] = field(default_factory=list)  # 参数列表
    implementation_class: str = ""      # 实现类路径（用于动态导入）
    enabled: bool = True                # 是否启用
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "key": self.key,
            "name": self.name,
            "model_type": self.model_type.value,
            "provider": self.provider.value,
            "description": self.description,
            "parameters": [
                {
                    "name": p.name,
                    "display_name": p.display_name,
                    "param_type": p.param_type,
                    "default_value": p.default_value,
                    "options": p.options,
                    "editable": p.editable,
                    "description": p.description,
                    "data_type": p.data_type.__name__ if p.data_type else "str"
                }
                for p in self.parameters
            ],
            "implementation_class": self.implementation_class,
            "enabled": self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ModelDefinition':
        """从字典创建"""
        params = []
        for p_data in data.get("parameters", []):
            param = ModelParameter(
                name=p_data["name"],
                display_name=p_data.get("display_name", p_data["name"]),
                param_type=p_data["param_type"],
                default_value=p_data.get("default_value"),
                options=p_data.get("options"),
                editable=p_data.get("editable", False),
                description=p_data.get("description", ""),
                data_type=eval(p_data.get("data_type", "str")) if "data_type" in p_data else str
            )
            params.append(param)
        
        return cls(
            key=data["key"],
            name=data["name"],
            model_type=ModelType(data["model_type"]),
            provider=ModelProvider(data["provider"]),
            description=data.get("description", ""),
            parameters=params,
            implementation_class=data.get("implementation_class", ""),
            enabled=data.get("enabled", True)
        )


class ModelRegistry:
    """
    模型注册表 - 解耦模型定义与实现
    
    功能：
    1. 管理所有模型定义（与具体实现分离）
    2. 支持动态添加/删除模型
    3. 提供统一的模型查询接口
    4. 支持从配置文件加载模型定义
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        # 存储模型定义: {model_type: {key: ModelDefinition}}
        self._definitions: Dict[ModelType, Dict[str, ModelDefinition]] = {
            model_type: {} for model_type in ModelType
        }
        
        # 存储模型实现类: {key: class}
        self._implementations: Dict[str, Type] = {}
        
        # 用户自定义模型目录
        self._custom_models_dir = Path("config/custom_models")
        self._custom_models_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载用户自定义模型
        self._load_custom_models()
    
    def register_model(self, definition: ModelDefinition, implementation_class: Type = None) -> bool:
        """
        注册模型
        
        Args:
            definition: 模型定义
            implementation_class: 模型实现类（可选，用于内置模型）
        
        Returns:
            bool: 是否注册成功
        """
        model_type = definition.model_type
        key = definition.key
        
        # 检查是否已存在
        if key in self._definitions[model_type]:
            print(f"模型 {key} 已存在，将被覆盖")
        
        # 注册定义
        self._definitions[model_type][key] = definition
        
        # 注册实现类
        if implementation_class is not None:
            self._implementations[key] = implementation_class
        
        # 如果是自定义模型，保存到文件
        if definition.provider == ModelProvider.CUSTOM:
            self._save_custom_model(definition)
        
        return True
    
    def unregister_model(self, model_type: ModelType, key: str) -> bool:
        """
        注销模型
        
        Args:
            model_type: 模型类型
            key: 模型标识
        
        Returns:
            bool: 是否注销成功
        """
        if key not in self._definitions[model_type]:
            return False
        
        # 删除定义
        del self._definitions[model_type][key]
        
        # 删除实现类引用
        if key in self._implementations:
            del self._implementations[key]
        
        # 删除自定义模型文件
        model_file = self._custom_models_dir / f"{key}.json"
        if model_file.exists():
            model_file.unlink()
        
        return True
    
    def get_model_definition(self, model_type: ModelType, key: str) -> Optional[ModelDefinition]:
        """获取模型定义"""
        return self._definitions[model_type].get(key)
    
    def get_model_definitions(self, model_type: ModelType) -> Dict[str, ModelDefinition]:
        """获取指定类型的所有模型定义"""
        return self._definitions[model_type].copy()
    
    def get_all_definitions(self) -> Dict[ModelType, Dict[str, ModelDefinition]]:
        """获取所有模型定义"""
        return {k: v.copy() for k, v in self._definitions.items()}
    
    def get_model_keys(self, model_type: ModelType) -> List[str]:
        """获取指定类型的所有模型键名"""
        return list(self._definitions[model_type].keys())
    
    def get_implementation_class(self, key: str) -> Optional[Type]:
        """获取模型实现类"""
        return self._implementations.get(key)
    
    def model_exists(self, model_type: ModelType, key: str) -> bool:
        """检查模型是否存在"""
        return key in self._definitions[model_type]
    
    def create_model_instance(self, model_type: ModelType, key: str, **params):
        """
        创建模型实例
        
        Args:
            model_type: 模型类型
            key: 模型标识
            **params: 实例化参数
        
        Returns:
            模型实例
        """
        definition = self.get_model_definition(model_type, key)
        if definition is None:
            raise ValueError(f"模型 {key} 未注册")
        
        impl_class = self.get_implementation_class(key)
        if impl_class is None:
            # 尝试动态导入
            if definition.implementation_class:
                impl_class = self._dynamic_import(definition.implementation_class)
                self._implementations[key] = impl_class
            else:
                raise ValueError(f"模型 {key} 没有实现类")
        
        return impl_class(**params)
    
    def _dynamic_import(self, class_path: str) -> Type:
        """动态导入类"""
        module_path, class_name = class_path.rsplit('.', 1)
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)
    
    def _save_custom_model(self, definition: ModelDefinition):
        """保存自定义模型到文件"""
        model_file = self._custom_models_dir / f"{definition.key}.json"
        with open(model_file, 'w', encoding='utf-8') as f:
            json.dump(definition.to_dict(), f, ensure_ascii=False, indent=2)
    
    def _load_custom_models(self):
        """加载用户自定义模型"""
        if not self._custom_models_dir.exists():
            return
        
        for model_file in self._custom_models_dir.glob("*.json"):
            try:
                with open(model_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                definition = ModelDefinition.from_dict(data)
                self._definitions[definition.model_type][definition.key] = definition
            except Exception as e:
                print(f"加载自定义模型 {model_file} 失败: {e}")
    
    def export_model_template(self, model_type: ModelType, output_path: str):
        """
        导出模型模板，供用户参考
        
        Args:
            model_type: 模型类型
            output_path: 输出路径
        """
        template = {
            "key": "my_custom_model",
            "name": "My Custom Model",
            "model_type": model_type.value,
            "provider": "custom",
            "description": "自定义模型描述",
            "parameters": [
                {
                    "name": "device",
                    "display_name": "Device",
                    "param_type": "selector",
                    "default_value": "cpu",
                    "options": ["cpu", "cuda", "mps"],
                    "editable": False,
                    "description": "运行设备",
                    "data_type": "str"
                },
                {
                    "name": "api_key",
                    "display_name": "API Key",
                    "param_type": "line_editor",
                    "default_value": "",
                    "editable": True,
                    "description": "API密钥",
                    "data_type": "str"
                }
            ],
            "implementation_class": "",
            "enabled": True
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)


# 全局注册表实例
model_registry = ModelRegistry()


def register_model_definition(
    key: str,
    name: str,
    model_type: ModelType,
    provider: ModelProvider = ModelProvider.LOCAL,
    description: str = "",
    parameters: List[ModelParameter] = None,
    implementation_class: str = "",
    enabled: bool = True
):
    """
    装饰器：注册模型定义
    
    用法：
        @register_model_definition(
            key="my_model",
            name="My Model",
            model_type=ModelType.OCR,
            ...
        )
        class MyModelClass:
            from modules.ocr import OCR_MODULES
        from modules.inpainter import INPAINTER_MODULES
        self.ocr_modules = OCR_MODULES
        self.inpainter_modules = INPAINTER_MODULES
    """
    def decorator(cls):
        definition = ModelDefinition(
            key=key,
            name=name,
            model_type=model_type,
            provider=provider,
            description=description,
            parameters=parameters or [],
            implementation_class=implementation_class or f"{cls.__module__}.{cls.__name__}",
            enabled=enabled
        )
        model_registry.register_model(definition, cls)
        return cls
    return decorator


# 兼容性函数：与原有代码兼容
def GET_VALID_TEXTDETECTORS() -> List[str]:
    """获取有效的文本检测器列表"""
    return model_registry.get_model_keys(ModelType.TEXT_DETECTOR)


def GET_VALID_OCR() -> List[str]:
    """获取有效的OCR列表"""
    return model_registry.get_model_keys(ModelType.OCR)


def GET_VALID_INPAINTERS() -> List[str]:
    """获取有效的修复器列表"""
    return model_registry.get_model_keys(ModelType.INPAINTER)


def GET_VALID_TRANSLATORS() -> List[str]:
    """获取有效的翻译器列表"""
    return model_registry.get_model_keys(ModelType.TRANSLATOR)


# ============ 兼容性模块注册对象 ============
# 为旧代码提供 module_register.module_dict 访问接口

class _ModuleDictCompat:
    """
    兼容性别名，将 model_registry._implementations 映射为旧代码期望的 module_dict 格式
    """
    def __init__(self, registry):
        self._registry = registry
    
    def __contains__(self, key):
        return key in self._registry._implementations
    
    def __getitem__(self, key):
        return self._registry._implementations[key]
    
    def keys(self):
        return self._registry._implementations.keys()
    
    def values(self):
        return self._registry._implementations.values()
    
    def items(self):
        return self._registry._implementations.items()
    
    def __iter__(self):
        return iter(self._registry._implementations)
    
    def get(self, key, default=None):
        return self._registry._implementations.get(key, default)
    
    def __len__(self):
        return len(self._registry._implementations)


class _ModuleRegisterCompat:
    """
    兼容性别名，提供旧代码期望的 module_register 接口
    """
    def __init__(self, registry):
        self._registry = registry
        self.module_dict = _ModuleDictCompat(registry)


# 全局 module_register 兼容性对象（供旧代码使用）
module_register = _ModuleRegisterCompat(model_registry)
