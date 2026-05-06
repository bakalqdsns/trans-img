> [!IMPORTANT]  
> **如打算公开分享本工具的机翻或自动生成内容，且未经过人工校对，请在显眼位置注明。**

# BallonTranslator (trans-img · Multimodal Edition)

一个**多模态图像文本处理与转换引擎**，支持从图像中提取、理解、转换并重构文本信息。  
可用于漫画翻译、图片文本重排、OCR数据处理、AI内容生成等场景。

---

<!-- IMAGE: 系统总览图 -->
<img src="doc/src/ui0.jpg" height="300">
<!-- 建议放：pipeline/架构图 -->
<p align=center>
系统结构概览
</p>

---

# 核心能力

## 多模态图文转换

支持完整链路：


Image → Detection → OCR → Text → Translation → Layout → Image


同时支持任意子路径：

- Image → Text（OCR）
- Text → Text（翻译 / 改写）
- Text → Image（嵌字 / 重排）
- Image → Image（去字 / 重绘）

👉 本质：**图像与文本之间的双向转换系统**

---

## 模块化架构（核心设计）

所有处理步骤完全解耦：

- Detection（文本检测）
- OCR（文本识别）
- Translation（翻译 / 改写）
- Rendering（排版 / 嵌字 / 重构）

每个模块均可：

- 独立运行
- 替换实现
- 跳过执行
- 接入外部服务 / 模型

---

## 标准中间表示（关键能力）

系统内部统一使用：


TextBlock (JSON)


结构描述图像中的文本信息：

- 文本内容
- 位置信息
- 字体 / 颜色
- 排版结构

👉 实现：

**任意模块之间的可插拔通信**

---

## LLM / AI 集成能力

支持接入：

- OpenAI 兼容 API  
- 本地大模型（如 Sakura / 自定义 LLM）  
- 任意文本处理模型  

可用于：

- 上下文翻译  
- 风格改写  
- 剧情重构  
- 自动润色  

---

# 应用场景

## 漫画翻译（原始功能）

- 自动识别气泡文本  
- 自动翻译并嵌字  
- 保持原排版风格  

---

## 图片文本提取（OCR）

- 批量提取图片文字  
- 输出结构化 JSON  

---

## 图像文本重排

- 修改文本内容  
- 自动重新排版  
- 生成新图片  

---

## 数据集生成

- OCR 标注数据生成  
- 图文对齐数据导出  

---

## AI内容生产

- 图片 → 文本 → 再生成图片  
- 多轮内容加工（Agent流程）  

---

# 系统流程

## 标准流程


Image
↓
文本检测
↓
OCR（可选）
↓
文本处理（翻译 / 改写 / LLM）
↓
排版重建
↓
输出图像


---

## 可组合流程（示例）

### 仅 OCR


Image → OCR → Text(JSON)


### 仅翻译


Text → Translation → Text


### 重排


Image → Text → Layout → Image


---

# 使用说明

## 快速启动（Windows）

下载预编译版本后运行：


launch_win.bat


---

## 源码运行

```bash
git clone https://github.com/dmMaze/BallonsTranslator.git
cd BallonsTranslator

python launch.py
模块控制（关键）
禁用 OCR
python launch.py --disable-ocr
禁用翻译
python launch.py --disable-translator
Headless（无GUI）
python launch.py --headless --exec_dirs "[DIR]"
扩展开发
模块接口
OCR

输入：

Image

输出：

TextBlock JSON
Translation

输入：

TextBlock / string

输出：

TextBlock（含译文）
自定义模型接入

开发者只需实现对应接口：

无需修改主流程
无需理解全部代码
界面
<!-- IMAGE: UI --> <p align=center> 主界面 </p>
<!-- IMAGE: OCR --> <p align=center> OCR效果 </p>
<!-- IMAGE: 文本编辑 --> <p align=center> 文本编辑 </p>
<!-- IMAGE: 修复 --> <p align=center> 图像修复 </p>
自动化模块

默认实现基于：

manga-image-translator

但当前版本已支持：

模块替换
多模型协同
自定义Pipeline
性能
GPU加速（CUDA / Apple Silicon）
AMD ROCm（实验支持）
项目定位（重要）

本项目不再只是：

❌ 漫画翻译工具

而是：

✅ 多模态图文转换引擎
✅ AI图文处理管线系统
✅ 可扩展内容生成基础设施

未来方向
Agent化自动处理（整本漫画 / 批量任务）
上下文理解（跨页翻译）
多模态生成（图文协同）
Web API / SaaS化
免责声明

本工具生成内容可能包含错误，仅供学习研究使用。
公开传播请标注“机翻/AI生成”。

致谢
manga-image-translator
各类 OCR / 翻译 / LLM 项目贡献者
