from typing import Tuple, List, Dict, Union, Callable, TYPE_CHECKING
import numpy as np
import cv2
from collections import OrderedDict

from utils.textblock import TextBlock
from ..model_registry import module_register, register_model_definition, ModelType, ModelProvider, ModelParameter
from ..base import DEFAULT_DEVICE, DEVICE_SELECTOR, LOGGER, register_hooks

if TYPE_CHECKING:
    from ..base import BaseModule



# ============ 兼容性装饰器 ============

def register_OCR(cls=None, *args, name=None, priority: int = 0):
    """
    兼容性装饰器，用于注册OCR模型。
    
    使用方式:
        @register_OCR
        class MyOCR(OCRBase):
            ...
        
        # 或指定名称
        @register_OCR(name="my_ocr")
        class MyOCR(OCRBase):
            ...
        
        # 或兼容旧写法
        @register_OCR('my_ocr')
        class MyOCR(OCRBase):
            ...
    
    在新代码中推荐使用 @register_model_definition 装饰器。
    """
    if isinstance(cls, str) and not args:
        name = cls
        cls = None

    def decorator(cls):
        from ..model_registry import register_model_definition, ModelType, ModelProvider
        
        # 自动生成 key 和 name
        key = name or cls.__name__.lower()
        display_name = name or cls.__name__.replace('_', ' ').title()
        
        # 如果类还没有被 register_model_definition 装饰，则自动注册
        if not hasattr(cls, '_model_definition'):
            register_model_definition(
                key=key,
                name=display_name,
                model_type=ModelType.OCR,
                provider=ModelProvider.LOCAL,
                description="",
                parameters=[]
            )(cls)
        
        return cls
    
    if cls is None:
        # @register_OCR(name="xxx") 或 @register_OCR('xxx') 形式
        return decorator
    else:
        # @register_OCR 直接使用形式
        return decorator(cls)


# ============ OCR 基础类 ============

class OCRBase:
    """
    OCR 模型基类。
    
    所有 OCR 模型都应继承此类并实现 _ocr_blk_list 和 ocr_img 方法。
    """
    
    download_file_list: List = None
    download_file_on_load = False
    _postprocess_hooks: Dict[str, Callable] = OrderedDict()
    _preprocess_hooks: Dict[str, Callable] = OrderedDict()
    _line_only: bool = False

    def __init__(self, **params) -> None:
        self.params = params or {}
        self.name = ''
        self._device = self.params.get('device', DEFAULT_DEVICE)
        self.params.setdefault('device', self._device)
        
        # 从 module_register 查找当前类的名称
        for key in module_register.module_dict:
            if module_register.module_dict[key] == self.__class__:
                self.name = key
                break

    @property
    def device(self) -> str:
        return self._device

    def get_param_value(self, param_key: str):
        """Get a parameter value from the OCR model params."""
        if self.params is None or param_key not in self.params:
            return None
        p = self.params[param_key]
        if isinstance(p, dict):
            return p.get('value')
        return p

    def set_param_value(self, param_key: str, param_value):
        """Set a parameter value in the OCR model params."""
        if self.params is None or param_key not in self.params:
            raise AssertionError(f'Parameter {param_key} not found')
        p = self.params[param_key]
        if isinstance(p, dict):
            p['value'] = param_value
        else:
            self.params[param_key] = param_value

    def run_ocr(self, img: np.ndarray, blk_list: List[TextBlock] = None, *args, **kwargs) -> Union[List[TextBlock], str]:

        if img.ndim == 3 and img.shape[-1] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)

        if blk_list is None:
            text = self.ocr_img(img)
            return text
        elif isinstance(blk_list, TextBlock):
            blk_list = [blk_list]

        for blk in blk_list:
            if self.name != 'none_ocr':
                blk.text = []
                
        self._ocr_blk_list(img, blk_list, *args, **kwargs)

        return blk_list

    def _ocr_blk_list(self, img: np.ndarray, blk_list: List[TextBlock], *args, **kwargs) -> None:
        """处理图像中的文本块列表"""
        raise NotImplementedError

    def ocr_img(self, img: np.ndarray) -> str:
        """对整个图像进行 OCR，返回识别的文本"""
        raise NotImplementedError
    
    def all_model_loaded(self) -> bool:
        """检查模型是否已加载"""
        return True
    
    def load_model(self) -> None:
        """加载模型（如果需要）"""
        pass
    
    @classmethod
    def get_postprocess_hook(cls, name: str) -> Callable:
        """获取后处理钩子"""
        return cls._postprocess_hooks.get(name)
    
    @classmethod
    def register_postprocess_hook(cls, name: str, hook: Callable) -> None:
        """注册后处理钩子"""
        cls._postprocess_hooks[name] = hook

    @classmethod
    def register_postprocess_hooks(cls, callbacks: Union[List, Callable, Dict]) -> None:
        """兼容旧接口：批量注册后处理钩子"""
        register_hooks(cls._postprocess_hooks, callbacks)

    @classmethod
    def register_preprocess_hooks(cls, callbacks: Union[List, Callable, Dict]) -> None:
        """兼容旧接口：批量注册预处理钩子"""
        register_hooks(cls._preprocess_hooks, callbacks)
