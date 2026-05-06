> [!IMPORTANT]  
> **如打算公开分享本工具的机翻结果，且没有有经验的译者进行过完整的翻译或校对，请在显眼位置注明机翻。**

# BallonTranslator (trans-img)

简体中文

深度学习辅助漫画翻译工具（模块化版本），支持一键机翻、OCR/翻译解耦、自定义模型接入与简单的图像/文本编辑  

<!-- IMAGE: UI预览 -->
<!-- 在此放界面截图 -->
<p align=center>
界面预览
</p>

---

# Features

* 一键机翻  
  - 支持模块化翻译流程（OCR 与翻译完全解耦）  
  - 译文回填参考原文排版（颜色 / 角度 / 对齐 / 气泡结构）  
  - 支持日漫 / 美漫  

* 模块化架构（本分支核心特性）  
  - OCR / 翻译 / 渲染 可独立启用或替换  
  - 支持接入任意第三方模型（本地 / API / LLM）  
  - 支持仅OCR / 仅翻译 / 全流程运行  

* 图像编辑  
  - 掩膜编辑  
  - 修复画笔  

* 文本编辑  
  - 所见即所得富文本编辑  
  - 批量排版与样式调整  
  - 查找替换（全文 / 原文 / 译文）  
  - 支持导入导出 Word  

* 适用于条漫 / 长图  

---

# 架构改动说明（trans-img）

本分支对原项目进行了**结构性重构（Decoupling）**：

## 核心变化

原流程（强耦合）：

检测 → OCR → 翻译 → 嵌字


新流程（模块化）：

检测 → OCR（可选） → 翻译（可选） → 渲染


👉 每个模块都可以：
- 独立运行
- 被替换
- 被跳过

---

## OCR 模块

- 与翻译逻辑完全解耦  
- 支持接入：
  - 本地OCR模型  
  - 第三方OCR服务  
- 输出统一结构（TextBlock）

---

## 翻译模块

- 统一接口抽象  
- 支持：
  - 本地模型（如 Sugoi / m2m100）  
  - API（DeepL / OpenAI兼容）  
  - LLM（自定义Prompt）  

- 支持脱离OCR运行（直接翻译已有文本）

---

## 渲染模块

- 保持原项目排版能力  
- 可仅作为「嵌字工具」使用  

---

# 使用说明

## Windows

如果不想手动配置环境：

从以下地址下载：
- MEGA
- Google Drive

解压后运行：

launch_win.bat


如模型下载失败，请手动下载 `data` 文件夹并放入目录。

---

## 运行源码

安装：

- Python <= 3.12  
- Git  

```bash
git clone https://github.com/dmMaze/BallonsTranslator.git
cd BallonsTranslator

python launch.py

更新：

python launch.py --update
模块化使用（重要）
仅 OCR
python launch.py --disable-translator
仅翻译
python launch.py --disable-ocr
仅嵌字（无AI）

关闭所有自动化模块后：

👉 Run 会基于已有文本重新排版

自定义模型接入

接口规范：

OCR输出：TextBlock JSON
翻译输入：TextBlock / string
翻译输出：TextBlock（含译文）

👉 新模型只需实现接口即可接入，无需修改核心代码

一键翻译
<!-- IMAGE: 运行演示 --> <!-- 放 gif -->

运行步骤：

打开图片文件夹
设置源语言 / 目标语言
点击 Run

等待完成即可

图像编辑
修复画笔
<!-- IMAGE: 修复画笔 --> <!-- 放 gif -->
矩形工具
<!-- IMAGE: 矩形工具 --> <!-- 放 gif -->
文本编辑
<!-- IMAGE: 文本编辑 --> <!-- 放 gif -->
快捷键

Ctrl+Z / Ctrl+Y：撤销 / 重做
A / D：翻页
T：文本模式
P：画板模式

Ctrl+F：查找
Ctrl+A：全选文本块

命令行模式
python launch.py --headless --exec_dirs "[DIR]"

参数：

--disable-ocr
--disable-translator
--ldpi
自动化模块

默认实现参考：

👉 manga-image-translator

但当前架构支持：

任意模块替换
独立运行
自定义组合
硬件加速
Nvidia GPU：默认启用 CUDA
Apple Silicon：支持
AMD：可通过 ROCm / ZLUDA
免责声明

本工具生成内容为机器翻译结果，仅供学习交流使用。
如用于公开传播，请明确标注“机翻”。

致谢
manga-image-translator
Sugoi Translator
各类 OCR / LLM 提供者
TODO（可选）
更稳定的多语言排版
更强的复杂背景修复
LLM上下文翻译优化
