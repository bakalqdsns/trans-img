#!/usr/bin/env python3
"""
BallonsTranslator 快速配置脚本
简化版本，不强制创建虚拟环境
"""

import os
import sys
import json
from pathlib import Path


def print_header(text: str):
    """打印标题"""
    print(f"\n{'='*60}")
    print(text)
    print(f"{'='*60}\n")


def print_success(text: str):
    """打印成功信息"""
    print(f"✓ {text}")


def print_error(text: str):
    """打印错误信息"""
    print(f"✗ {text}")


def print_warning(text: str):
    """打印警告信息"""
    print(f"⚠ {text}")


def print_info(text: str):
    """打印信息"""
    print(f"ℹ {text}")


def main():
    """主函数"""
    print_header("BallonsTranslator 快速配置")
    
    project_root = Path(__file__).parent.parent.absolute()
    print_info(f"项目路径: {project_root}")
    
    # 1. 检查Python版本
    print_info("检查Python版本...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python版本过低: {version.major}.{version.minor}")
        print_info("需要 Python 3.8 或更高版本")
        return 1
    print_success(f"Python版本: {version.major}.{version.minor}.{version.micro}")
    
    # 2. 检查项目结构
    print_info("检查项目结构...")
    required_dirs = ["modules", "ui", "utils", "config"]
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print_success(f"目录存在: {dir_name}/")
        else:
            print_error(f"目录缺失: {dir_name}/")
    
    # 3. 设置配置目录
    print_info("设置配置目录...")
    custom_models_dir = project_root / "config" / "custom_models"
    custom_models_dir.mkdir(parents=True, exist_ok=True)
    print_success(f"自定义模型目录: {custom_models_dir}")
    
    # 4. 创建示例模型
    print_info("检查示例模型...")
    example_files = list(custom_models_dir.glob("example_*.json"))
    if len(example_files) >= 4:
        print_success(f"已有 {len(example_files)} 个示例模型文件")
    else:
        print_info("创建示例模型文件...")
        create_example_models(custom_models_dir)
    
    # 5. 测试模型注册表
    print_info("测试模型注册表...")
    test_model_registry(project_root, custom_models_dir)
    
    # 6. 打印使用说明
    print_header("配置完成")
    
    print("启动方式:")
    print(f"  cd {project_root}")
    print("  python3 launch.py")
    print("")
    print("添加自定义模型:")
    print(f"  1. 将JSON文件放入: {custom_models_dir}")
    print("  2. 参考示例文件格式")
    print("  3. 重启应用")
    print("")
    print("测试模型注册表:")
    print("  python3 tests/test_model_registry_core.py")
    print("")
    print("="*60)
    print("配置完成！可以开始使用了。")
    print("="*60)
    
    return 0


def create_example_models(custom_models_dir: Path):
    """创建示例模型文件"""
    
    examples = {
        "example_custom_openai.json": {
            "key": "custom_openai_api",
            "name": "自定义OpenAI API",
            "model_type": "translator",
            "provider": "custom",
            "description": "用户自定义的OpenAI兼容API翻译服务",
            "parameters": [
                {
                    "name": "api_url",
                    "display_name": "API地址",
                    "param_type": "line_editor",
                    "default_value": "https://api.openai.com/v1/chat/completions",
                    "editable": True,
                    "description": "OpenAI API的完整URL",
                    "data_type": "str"
                },
                {
                    "name": "api_key",
                    "display_name": "API密钥",
                    "param_type": "line_editor",
                    "default_value": "",
                    "editable": True,
                    "description": "您的API密钥",
                    "data_type": "str"
                },
                {
                    "name": "model",
                    "display_name": "模型名称",
                    "param_type": "line_editor",
                    "default_value": "gpt-3.5-turbo",
                    "editable": True,
                    "description": "使用的模型名称",
                    "data_type": "str"
                },
                {
                    "name": "temperature",
                    "display_name": "Temperature",
                    "param_type": "line_editor",
                    "default_value": "0.7",
                    "editable": True,
                    "description": "生成文本的随机性 (0-2)",
                    "data_type": "float"
                },
                {
                    "name": "max_tokens",
                    "display_name": "最大Token数",
                    "param_type": "line_editor",
                    "default_value": "2000",
                    "editable": True,
                    "description": "每次请求的最大token数",
                    "data_type": "int"
                },
                {
                    "name": "timeout",
                    "display_name": "超时时间(秒)",
                    "param_type": "line_editor",
                    "default_value": "30",
                    "editable": True,
                    "description": "API请求超时时间",
                    "data_type": "int"
                }
            ],
            "implementation_class": "",
            "enabled": True
        },
        
        "example_custom_ocr.json": {
            "key": "custom_ocr_api",
            "name": "自定义OCR API",
            "model_type": "ocr",
            "provider": "custom",
            "description": "用户自定义的OCR API服务",
            "parameters": [
                {
                    "name": "api_url",
                    "display_name": "API地址",
                    "param_type": "line_editor",
                    "default_value": "http://localhost:8080/ocr",
                    "editable": True,
                    "description": "OCR服务的API地址",
                    "data_type": "str"
                },
                {
                    "name": "api_key",
                    "display_name": "API密钥",
                    "param_type": "line_editor",
                    "default_value": "",
                    "editable": True,
                    "description": "API认证密钥（如果需要）",
                    "data_type": "str"
                },
                {
                    "name": "language",
                    "display_name": "识别语言",
                    "param_type": "selector",
                    "default_value": "auto",
                    "options": ["auto", "zh", "en", "ja", "ko"],
                    "editable": True,
                    "description": "OCR识别的目标语言",
                    "data_type": "str"
                },
                {
                    "name": "use_gpu",
                    "display_name": "使用GPU",
                    "param_type": "checkbox",
                    "default_value": False,
                    "editable": True,
                    "description": "是否使用GPU加速",
                    "data_type": "bool"
                }
            ],
            "implementation_class": "",
            "enabled": True
        },
        
        "example_custom_api_ocr.json": {
            "key": "custom_api_ocr",
            "name": "自定义API OCR",
            "model_type": "ocr",
            "provider": "api",
            "description": "用户自定义的OCR API服务",
            "parameters": [
                {
                    "name": "api_url",
                    "display_name": "API地址",
                    "param_type": "line_editor",
                    "default_value": "http://localhost:8080/ocr",
                    "editable": True,
                    "description": "OCR服务的API地址",
                    "data_type": "str"
                },
                {
                    "name": "api_key",
                    "display_name": "API密钥",
                    "param_type": "line_editor",
                    "default_value": "",
                    "editable": True,
                    "description": "API认证密钥（如果需要）",
                    "data_type": "str"
                },
                {
                    "name": "language",
                    "display_name": "识别语言",
                    "param_type": "selector",
                    "default_value": "auto",
                    "options": ["auto", "zh", "en", "ja", "ko"],
                    "editable": True,
                    "description": "OCR识别的目标语言",
                    "data_type": "str"
                },
                {
                    "name": "timeout",
                    "display_name": "超时时间(秒)",
                    "param_type": "line_editor",
                    "default_value": "30",
                    "editable": True,
                    "description": "API请求超时时间",
                    "data_type": "int"
                }
            ],
            "implementation_class": "",
            "enabled": True
        },
        
        "example_custom_llm_translator.json": {
            "key": "custom_llm_translator",
            "name": "自定义LLM翻译器",
            "model_type": "translator",
            "provider": "api",
            "description": "用户自定义的LLM翻译服务",
            "parameters": [
                {
                    "name": "api_url",
                    "display_name": "API地址",
                    "param_type": "line_editor",
                    "default_value": "http://localhost:8000/v1/chat/completions",
                    "editable": True,
                    "description": "LLM API的完整URL",
                    "data_type": "str"
                },
                {
                    "name": "api_key",
                    "display_name": "API密钥",
                    "param_type": "line_editor",
                    "default_value": "",
                    "editable": True,
                    "description": "API认证密钥",
                    "data_type": "str"
                },
                {
                    "name": "model",
                    "display_name": "模型名称",
                    "param_type": "selector",
                    "default_value": "default",
                    "options": ["default", "gpt-3.5-turbo", "gpt-4", "claude-3"],
                    "editable": True,
                    "description": "使用的模型名称",
                    "data_type": "str"
                },
                {
                    "name": "temperature",
                    "display_name": "Temperature",
                    "param_type": "line_editor",
                    "default_value": "0.3",
                    "editable": True,
                    "description": "生成文本的随机性",
                    "data_type": "float"
                },
                {
                    "name": "max_tokens",
                    "display_name": "最大Token数",
                    "param_type": "line_editor",
                    "default_value": "1000",
                    "editable": True,
                    "description": "每次请求的最大token数",
                    "data_type": "int"
                },
                {
                    "name": "system_prompt",
                    "display_name": "系统提示词",
                    "param_type": "editor",
                    "default_value": "You are a professional translator. Translate the following text accurately.",
                    "editable": True,
                    "description": "系统提示词",
                    "data_type": "str"
                },
                {
                    "name": "use_context",
                    "display_name": "使用上下文",
                    "param_type": "checkbox",
                    "default_value": True,
                    "editable": True,
                    "description": "是否使用上下文信息",
                    "data_type": "bool"
                }
            ],
            "implementation_class": "",
            "enabled": True
        }
    }
    
    for filename, data in examples.items():
        filepath = custom_models_dir / filename
        if not filepath.exists():
            filepath.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            print_success(f"创建: {filename}")


def test_model_registry(project_root: Path, custom_models_dir: Path):
    """测试模型注册表"""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "model_registry",
            project_root / "modules" / "model_registry.py"
        )
        model_registry_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(model_registry_module)
        
        # 创建注册表实例
        registry = model_registry_module.ModelRegistry.__new__(
            model_registry_module.ModelRegistry
        )
        registry._initialized = True
        registry._definitions = {mt: {} for mt in model_registry_module.ModelType}
        registry._implementations = {}
        
        # 加载自定义模型
        if custom_models_dir.exists():
            for json_file in custom_models_dir.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    definition = model_registry_module.ModelDefinition.from_dict(data)
                    registry._definitions[definition.model_type][definition.key] = definition
                except Exception as e:
                    print_warning(f"加载 {json_file.name} 失败: {e}")
        
        # 统计模型
        total = 0
        for model_type in model_registry_module.ModelType:
            count = len(registry._definitions[model_type])
            if count > 0:
                print_success(f"  {model_type.value}: {count} 个模型")
                total += count
        
        if total > 0:
            print_success(f"总计: {total} 个自定义模型")
        else:
            print_warning("没有找到自定义模型")
        
        return True
    except Exception as e:
        print_error(f"测试失败: {e}")
        return False


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n配置失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
