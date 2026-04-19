#!/usr/bin/env python3
"""
BallonsTranslator 本地运行配置脚本
自动设置环境、安装依赖、验证模型注册表系统
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import List, Tuple, Optional


class Colors:
    """终端颜色"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """打印标题"""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}\n")


def print_success(text: str):
    """打印成功信息"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    """打印错误信息"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_warning(text: str):
    """打印警告信息"""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_info(text: str):
    """打印信息"""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def run_command(cmd: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


class SetupManager:
    """设置管理器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.absolute()
        self.venv_path = self.project_root / "venv"
        self.requirements_file = self.project_root / "requirements.txt"
        self.config_dir = self.project_root / "config"
        self.custom_models_dir = self.config_dir / "custom_models"
        
    def check_python_version(self) -> bool:
        """检查Python版本"""
        print_info("检查Python版本...")
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print_error(f"Python版本过低: {version.major}.{version.minor}")
            print_info("需要 Python 3.8 或更高版本")
            return False
        print_success(f"Python版本: {version.major}.{version.minor}.{version.micro}")
        return True
    
    def check_project_structure(self) -> bool:
        """检查项目结构"""
        print_info("检查项目结构...")
        
        required_dirs = [
            "modules",
            "ui",
            "utils",
            "config",
        ]
        
        all_exist = True
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                print_success(f"目录存在: {dir_name}/")
            else:
                print_error(f"目录缺失: {dir_name}/")
                all_exist = False
        
        return all_exist
    
    def create_virtual_environment(self) -> bool:
        """创建虚拟环境"""
        print_info("创建虚拟环境...")
        
        if self.venv_path.exists():
            print_warning("虚拟环境已存在")
            return True
        
        try:
            import venv
            venv.create(self.venv_path, with_pip=True)
            print_success(f"虚拟环境创建成功: {self.venv_path}")
            return True
        except Exception as e:
            print_error(f"创建虚拟环境失败: {e}")
            return False
    
    def get_pip_cmd(self) -> str:
        """获取pip命令路径"""
        if os.name == 'nt':  # Windows
            return str(self.venv_path / "Scripts" / "pip.exe")
        else:  # Linux/Mac
            return str(self.venv_path / "bin" / "pip")
    
    def get_python_cmd(self) -> str:
        """获取python命令路径"""
        if os.name == 'nt':  # Windows
            return str(self.venv_path / "Scripts" / "python.exe")
        else:  # Linux/Mac
            return str(self.venv_path / "bin" / "python")
    
    def install_dependencies(self) -> bool:
        """安装依赖"""
        print_info("安装依赖...")
        
        # 基础依赖列表
        base_packages = [
            "termcolor",
            "numpy",
            "pillow",
            "requests",
        ]
        
        pip_cmd = self.get_pip_cmd()
        
        # 升级pip
        returncode, _, _ = run_command([pip_cmd, "install", "--upgrade", "pip"])
        if returncode != 0:
            print_warning("pip升级失败，继续安装...")
        
        # 安装基础依赖
        all_success = True
        for package in base_packages:
            print_info(f"  安装 {package}...")
            returncode, stdout, stderr = run_command([pip_cmd, "install", package])
            if returncode == 0:
                print_success(f"  {package} 安装成功")
            else:
                print_error(f"  {package} 安装失败")
                print(f"    {stderr[:200]}")
                all_success = False
        
        # 尝试安装requirements.txt
        if self.requirements_file.exists():
            print_info("安装 requirements.txt 中的依赖...")
            returncode, stdout, stderr = run_command(
                [pip_cmd, "install", "-r", str(self.requirements_file)]
            )
            if returncode == 0:
                print_success("requirements.txt 安装成功")
            else:
                print_warning("requirements.txt 安装失败（部分依赖可能不需要）")
        
        return all_success
    
    def setup_config_directory(self) -> bool:
        """设置配置目录"""
        print_info("设置配置目录...")
        
        # 创建自定义模型目录
        self.custom_models_dir.mkdir(parents=True, exist_ok=True)
        print_success(f"自定义模型目录: {self.custom_models_dir}")
        
        # 创建示例模型文件
        example_files = list(self.custom_models_dir.glob("example_*.json"))
        if not example_files:
            print_info("创建示例模型文件...")
            self.create_example_models()
        else:
            print_success(f"已有 {len(example_files)} 个示例模型文件")
        
        return True
    
    def create_example_models(self):
        """创建示例模型文件"""
        
        # OpenAI API示例
        openai_example = {
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
                }
            ],
            "implementation_class": "",
            "enabled": True
        }
        
        # OCR API示例
        ocr_example = {
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
                }
            ],
            "implementation_class": "",
            "enabled": True
        }
        
        # 保存示例文件
        (self.custom_models_dir / "example_custom_openai.json").write_text(
            json.dumps(openai_example, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        (self.custom_models_dir / "example_custom_ocr.json").write_text(
            json.dumps(ocr_example, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        
        print_success("示例模型文件创建完成")
    
    def test_model_registry(self) -> bool:
        """测试模型注册表"""
        print_info("测试模型注册表核心功能...")
        
        # 直接导入测试，避免依赖链
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "model_registry",
            self.project_root / "modules" / "model_registry.py"
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
        registry._custom_models_dir = self.custom_models_dir
        
        # 加载自定义模型
        if self.custom_models_dir.exists():
            for json_file in self.custom_models_dir.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    definition = model_registry_module.ModelDefinition.from_dict(data)
                    registry._definitions[definition.model_type][definition.key] = definition
                except Exception as e:
                    print_warning(f"加载 {json_file.name} 失败: {e}")
        
        # 统计模型
        total_models = 0
        for model_type in model_registry_module.ModelType:
            count = len(registry._definitions[model_type])
            if count > 0:
                print_success(f"  {model_type.value}: {count} 个模型")
                total_models += count
        
        if total_models == 0:
            print_warning("没有找到自定义模型")
        else:
            print_success(f"总计: {total_models} 个自定义模型")
        
        return True
    
    def create_launcher_scripts(self):
        """创建启动脚本"""
        print_info("创建启动脚本...")
        
        scripts_dir = self.project_root / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        
        # Windows启动脚本
        windows_launcher = scripts_dir / "launch.bat"
        windows_content = f"""@echo off
chcp 65001 >nul
cd /d "{self.project_root}"
call "{self.venv_path}\\Scripts\\activate.bat"
python launch.py %*
pause
"""
        windows_launcher.write_text(windows_content, encoding='utf-8')
        print_success(f"Windows启动脚本: {windows_launcher}")
        
        # Linux/Mac启动脚本
        unix_launcher = scripts_dir / "launch.sh"
        unix_content = f"""#!/bin/bash
cd "{self.project_root}"
source "{self.venv_path}/bin/activate"
python launch.py "$@"
"""
        unix_launcher.write_text(unix_content, encoding='utf-8')
        unix_launcher.chmod(0o755)  # 添加执行权限
        print_success(f"Linux/Mac启动脚本: {unix_launcher}")
    
    def print_summary(self):
        """打印总结"""
        print_header("配置完成总结")
        
        print(f"{Colors.BOLD}项目路径:{Colors.ENDC} {self.project_root}")
        print(f"{Colors.BOLD}虚拟环境:{Colors.ENDC} {self.venv_path}")
        print(f"{Colors.BOLD}Python命令:{Colors.ENDC} {self.get_python_cmd()}")
        print(f"{Colors.BOLD}自定义模型目录:{Colors.ENDC} {self.custom_models_dir}")
        
        print(f"\n{Colors.BOLD}启动方式:{Colors.ENDC}")
        print(f"  1. 使用启动脚本:")
        if os.name == 'nt':
            print(f"     scripts\\launch.bat")
        else:
            print(f"     ./scripts/launch.sh")
        print(f"  2. 手动启动:")
        print(f"     {self.get_python_cmd()} launch.py")
        
        print(f"\n{Colors.BOLD}添加自定义模型:{Colors.ENDC}")
        print(f"  1. 将JSON文件放入: {self.custom_models_dir}")
        print(f"  2. 参考示例: example_*.json")
        print(f"  3. 重启应用")
        
        print(f"\n{Colors.OKGREEN}{'='*60}{Colors.ENDC}")
        print(f"{Colors.OKGREEN}配置完成！可以开始使用了。{Colors.ENDC}")
        print(f"{Colors.OKGREEN}{'='*60}{Colors.ENDC}\n")
    
    def run(self):
        """运行完整配置流程"""
        print_header("BallonsTranslator 本地运行配置")
        
        steps = [
            ("检查Python版本", self.check_python_version),
            ("检查项目结构", self.check_project_structure),
            ("创建虚拟环境", self.create_virtual_environment),
            ("安装依赖", self.install_dependencies),
            ("设置配置目录", self.setup_config_directory),
            ("测试模型注册表", self.test_model_registry),
            ("创建启动脚本", self.create_launcher_scripts),
        ]
        
        failed_steps = []
        
        for step_name, step_func in steps:
            print(f"\n{Colors.BOLD}[{steps.index((step_name, step_func)) + 1}/{len(steps)}] {step_name}{Colors.ENDC}")
            try:
                success = step_func()
                if not success:
                    failed_steps.append(step_name)
                    print_error(f"{step_name} 失败")
            except Exception as e:
                failed_steps.append(step_name)
                print_error(f"{step_name} 出错: {e}")
                import traceback
                traceback.print_exc()
        
        # 打印总结
        self.print_summary()
        
        if failed_steps:
            print_warning(f"以下步骤未完成: {', '.join(failed_steps)}")
            print_info("某些功能可能受限，但核心功能应该可以工作")
        
        return len(failed_steps) == 0


def main():
    """主函数"""
    try:
        manager = SetupManager()
        success = manager.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}配置失败: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
