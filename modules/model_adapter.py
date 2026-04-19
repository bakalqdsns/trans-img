# Model Adapter - 模型适配器
# 将新模型注册表与原有系统无缝集成

"""
适配器模式：将新的ModelRegistry与原有ModuleConfigParseWidget等组件集成
实现模型依赖的完全解耦和动态录入
"""

from typing import Dict, List, Optional, Any, Callable
import json
from pathlib import Path

# 导入新架构
from .model_registry import (
    ModelRegistry, ModelDefinition, ModelParameter,
    ModelType, ModelProvider, model_registry
)

# 导入原有组件
from .base import BaseModule, DEVICE_SELECTOR, LOGGER
from utils.registry import Registry


class ModelAdapter:
    """
    模型适配器 - 桥接新旧架构
    
    功能：
    1. 将原有Registry中的模型迁移到ModelRegistry
    2. 提供统一的模型查询接口
    3. 支持动态模型录入
    4. 保持与原有代码的兼容性
    """
    
    def __init__(self):
        self._migration_done = False
        self._model_type_map = {
            'textdetector': ModelType.TEXT_DETECTOR,
            'ocr': ModelType.OCR,
            'inpainter': ModelType.INPAINTER,
            'translator': ModelType.TRANSLATOR,
        }
    
    def migrate_from_registry(self, 
                              registry: Registry, 
                              model_type: ModelType,
                              param_extraction_func: Callable = None):
        """
        从原有Registry迁移模型到ModelRegistry
        
        Args:
            registry: 原有Registry实例
            model_type: 模型类型
            param_extraction_func: 参数提取函数
        """
        for key, cls in registry.module_dict.items():
            if model_registry.model_exists(model_type, key):
                continue
            
            # 提取参数定义
            params = getattr(cls, 'params', None) or {}
            parameters = self._extract_parameters(params)
            
            # 创建模型定义
            definition = ModelDefinition(
                key=key,
                name=getattr(cls, 'name', key),
                model_type=model_type,
                provider=ModelProvider.LOCAL,
                description=getattr(cls, '__doc__', ''),
                parameters=parameters,
                implementation_class=f"{cls.__module__}.{cls.__name__}",
                enabled=True
            )
            
            model_registry.register_model(definition, cls)
            LOGGER.info(f"已迁移模型: {key} ({model_type.value})")
    
    def _extract_parameters(self, params: Dict) -> List[ModelParameter]:
        """从原有参数格式提取参数定义"""
        parameters = []
        
        for param_name, param_value in params.items():
            if param_name.startswith('__') or param_name == 'description':
                continue
            
            if isinstance(param_value, dict):
                param = ModelParameter(
                    name=param_name,
                    display_name=param_value.get('display_name', param_name),
                    param_type=param_value.get('type', 'line_editor'),
                    default_value=param_value.get('value', ''),
                    options=param_value.get('options'),
                    editable=param_value.get('editable', False),
                    description=param_value.get('description', ''),
                    data_type=param_value.get('data_type', str)
                )
            else:
                param = ModelParameter(
                    name=param_name,
                    display_name=param_name,
                    param_type='line_editor',
                    default_value=param_value,
                )
            parameters.append(param)
        
        return parameters
    
    def get_model_params_dict(self, model_type: ModelType, key: str) -> Optional[Dict]:
        """
        获取模型参数字典（兼容原有格式）
        
        Returns:
            原有格式的参数字典
        """
        definition = model_registry.get_model_definition(model_type, key)
        if not definition:
            return None
        
        params = {}
        for param in definition.parameters:
            if param.param_type == 'selector':
                params[param.name] = {
                    'type': 'selector',
                    'options': param.options or [],
                    'value': param.default_value,
                    'editable': param.editable,
                    'description': param.description,
                }
            elif param.param_type == 'checkbox':
                params[param.name] = {
                    'type': 'checkbox',
                    'value': param.default_value,
                    'description': param.description,
                }
            elif param.param_type == 'editor':
                params[param.name] = {
                    'type': 'editor',
                    'value': param.default_value,
                    'description': param.description,
                }
            else:
                params[param.name] = param.default_value
        
        if definition.description:
            params['description'] = definition.description
        
        return params
    
    def create_model_instance(self, 
                              model_type: ModelType, 
                              key: str, 
                              **kwargs) -> Optional[BaseModule]:
        """创建模型实例"""
        try:
            return model_registry.create_model_instance(model_type, key, **kwargs)
        except Exception as e:
            LOGGER.error(f"创建模型实例失败 {key}: {e}")
            return None
    
    def get_valid_models(self, model_type: ModelType) -> List[str]:
        """获取有效的模型列表"""
        return model_registry.get_model_keys(model_type)


# 全局适配器实例
model_adapter = ModelAdapter()


def migrate_all_modules():
    """迁移所有模块到新的注册表"""
    # 导入旧的Registry对象进行迁移
    from .textdetector.base import TEXTDETECTORS as old_textdetectors
    from .inpaint.base import INPAINTERS as old_inpainters
    
    # translators没有旧Registry，使用新创建的
    from utils.registry import Registry
    old_translators = Registry('translators')
    try:
        from .translators import trans_baidu, trans_caiyun, trans_chatgpt, trans_chatgpt_exp, trans_deepl, trans_deeplx, trans_deeplx_api, trans_eztrans, trans_google, trans_llm_api, trans_m2m100, trans_papago, trans_sakura, trans_sugoi, trans_tgw, trans_trnslatorsmodule, trans_yandex, trans_yandex_foswly, trans_youdao_api, module_eztrans32
    except ImportError:
        pass
    
    model_adapter.migrate_from_registry(old_textdetectors, ModelType.TEXT_DETECTOR)
    model_adapter.migrate_from_registry(old_inpainters, ModelType.INPAINTER)
    model_adapter.migrate_from_registry(old_translators, ModelType.TRANSLATOR)
    
    LOGGER.info("所有模型已迁移到新的注册表系统")


# 兼容性函数 - 与原有代码兼容
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


def get_model_params(model_type_str: str, key: str) -> Optional[Dict]:
    """
    获取模型参数
    
    Args:
        model_type_str: 'textdetector', 'ocr', 'inpainter', 'translator'
        key: 模型标识
    """
    type_map = {
        'textdetector': ModelType.TEXT_DETECTOR,
        'ocr': ModelType.OCR,
        'inpainter': ModelType.INPAINTER,
        'translator': ModelType.TRANSLATOR,
    }
    
    model_type = type_map.get(model_type_str)
    if not model_type:
        return None
    
    return model_adapter.get_model_params_dict(model_type, key)


def register_custom_model(definition: ModelDefinition):
    """
    注册自定义模型
    
    供用户动态录入新模型使用
    """
    definition.provider = ModelProvider.CUSTOM
    return model_registry.register_model(definition)


def export_model_template(model_type: ModelType, output_path: str):
    """导出模型模板供用户参考"""
    model_registry.export_model_template(model_type, output_path)
