from .base import *


# 导入所有文本检测器模型
from . import detector_ctd
from . import detector_ysg
from . import detector_stariver


class _TextDetectorRegistryCompat:
    """
    兼容性层名，提供旧代码期望的 TextDetector Registry 接口
    """
    def __init__(self):
        from ..model_registry import model_registry, ModelType
        self._registry = model_registry
        self._type = ModelType.TEXT_DETECTOR
    
    @property
    def module_dict(self):
        """返回 TEXT_DETECTOR 类型的已注册模块字典"""
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


# TextDetector 兼容性 Registry 对象（供旧代码使用）
TEXTDETECTORS = _TextDetectorRegistryCompat()


def get_text_detector(key: str, **params):
    """
    获取文本检测器模型实例
    
    Args:
        key: 模型标识
        **params: 模型参数
    
    Returns:
        文本检测器模型实例
    """
    from ..model_registry import model_registry, ModelType
    
    # 创建模型实例
    model = model_registry.create_model_instance(ModelType.TEXT_DETECTOR, key, **params)
    
    # 加载模型（如果需要）
    if hasattr(model, 'load_model'):
        model.load_model()
    
    return model