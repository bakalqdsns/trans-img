from .base import OCRBase, register_OCR, DEVICE_SELECTOR, DEFAULT_DEVICE, TextBlock
from ..model_registry import model_registry, ModelType


# 导入所有OCR模型
from . import ocr_mit
from . import ocr_none
from . import ocr_bing_lens
from . import ocr_google_vision
from . import ocr_lens_proto
from . import ocr_llm_api
from . import ocr_macos
from . import ocr_manga
from . import ocr_oneocr
from . import ocr_paddle
from . import ocr_paddleVL_manga
from . import ocr_paddle_VL
from . import ocr_stariver
from . import ocr_windows


class _OCRRegistryCompat:
    """
    兼容性别名，提供旧代码期望的 OCR Registry 接口
    """
    def __init__(self):
        self._registry = model_registry
        self._type = ModelType.OCR
    
    @property
    def module_dict(self):
        """返回 OCR 类型的已注册模块字典"""
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


# OCR 兼容性 Registry 对象（供旧代码使用）
OCR = _OCRRegistryCompat()


def get_ocr_model(key: str, **params):
    """
    获取OCR模型实例
    
    Args:
        key: 模型标识
        **params: 模型参数
    
    Returns:
        OCR模型实例
    """
    from ..model_registry import model_registry, ModelType
    
    # 创建模型实例
    model = model_registry.create_model_instance(ModelType.OCR, key, **params)
    
    # 加载模型（如果需要）
    if hasattr(model, 'load_model'):
        model.load_model()
    
    return model
