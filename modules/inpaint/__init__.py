from .base import *


# 导入所有修复器模型
from . import lama
from . import aot
from . import ffc
try:
    from . import patch_match
except (ImportError, OSError):
    # patch_match requires libpatchmatch.so which may not be available
    patch_match = None


class _InpainterRegistryCompat:
    """
    兼容性层名，提供旧代码期望的 Inpainter Registry 接口
    """
    def __init__(self):
        from ..model_registry import model_registry, ModelType
        self._registry = model_registry
        self._type = ModelType.INPAINTER
    
    @property
    def module_dict(self):
        """返回 INPAINTER 类型的已注册模块字典"""
        result = {}
        for key, model_def in self._registry._definitions.get(self._type, {}).items():
            impl = self._registry._implementations.get(key)
            if impl is not None:
                result[key] = impl
        return result
    
    def get(self, key, default=None):
        return self.module_dict.get(key, default)
    
    def __getitem__(self, key):
        return self._registry._implementations[key]
    
    def __contains__(self, key):
        return key in self.module_dict
    
    def keys(self):
        return self.module_dict.keys()
    
    def values(self):
        return self.module_dict.values()
    
    def items(self):
        return self.module_dict.items()


# Inpainter 兼容性 Registry 对象（供旧代码使用）
INPAINTERS = _InpainterRegistryCompat()


def get_inpainter(key: str, **params):
    """
    获取修复器模型实例
    
    Args:
        key: 模型标识
        **params: 模型参数
    
    Returns:
        修复器模型实例
    """
    from ..model_registry import model_registry, ModelType
    
    # 创建模型实例
    model = model_registry.create_model_instance(ModelType.INPAINTER, key, **params)
    
    # 加载模型（如果需要）
    if hasattr(model, 'load_model'):
        model.load_model()
    
    return model