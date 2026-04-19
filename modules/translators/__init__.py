from .base import *
from ..model_registry import model_registry, ModelType


# 导入所有翻译器模型
from . import trans_baidu
from . import trans_caiyun
from . import trans_chatgpt
from . import trans_chatgpt_exp
from . import trans_deepl
from . import trans_deeplx
from . import trans_deeplx_api
from . import trans_eztrans
from . import trans_google
from . import trans_llm_api
from . import trans_m2m100
from . import trans_papago
from . import trans_sakura
from . import trans_sugoi
from . import trans_tgw
from . import trans_trnslatorsmodule
from . import trans_yandex
from . import trans_yandex_foswly
from . import trans_youdao_api
try:
    from . import module_eztrans32
except ImportError:
    # msl.loadlib not installed, module_eztrans32 unavailable
    module_eztrans32 = None


class _TranslatorRegistryCompat:
    """
    兼容性别名，提供旧代码期望的 Translator Registry 接口
    """
    def __init__(self):
        self._registry = model_registry
        self._type = ModelType.TRANSLATOR

    @property
    def module_dict(self):
        """返回 Translator 类型的已注册模块字典"""
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


TRANSLATORS = _TranslatorRegistryCompat()


def get_translator(key: str, **params):
    """
    获取翻译器模型实例
    
    Args:
        key: 模型标识
        **params: 模型参数
    
    Returns:
        翻译器模型实例
    """
    from ..model_registry import model_registry, ModelType
    
    # 为翻译器提供默认的语言参数
    if 'lang_source' not in params:
        params['lang_source'] = 'Auto'
    if 'lang_target' not in params:
        params['lang_target'] = '简体中文'
    
    # 创建模型实例
    model = model_registry.create_model_instance(ModelType.TRANSLATOR, key, **params)
    
    # 加载模型（如果需要）
    if hasattr(model, 'load_model'):
        model.load_model()
    
    return model