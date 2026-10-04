# LocalLecture

[English](README.md) | [简体中文](README.zh-CN.md)

第一版：本地课堂录音 → 带时间戳转写 → 主题分段 → PDF/PPTX 解析 → 课件对齐 → 分段笔记 → 证据核验 → Markdown / Gradio。自行组织 pipeline，不使用 LangChain，不加入 SQLite。

## 运行

Python 3.11 / 3.12。在项目根目录执行：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
ollama pull qwen3:4b
# 如果 Ollama 尚未启动，在另一个终端运行 ollama serve
python -m src.pipeline --audio data/raw/audio/lecture.mp3 --slides data/raw/slides/lecture.pdf --title "COMPxxxx — Neural Networks" --config config/config.yaml
python -m app.gradio_app
```

Qwen3 8B 实验可将配置中的 `ollama_model` 改为 `qwen3:8b`，并先拉取该模型。默认 Whisper 使用 CPU / int8；GPU 配置与运行库需按 faster-whisper 文档设置。

首次使用 Whisper 和 sentence-transformers 会下载模型；缓存模型并准备好 Ollama 后可本地运行。模型大小与首次运行时间取决于配置及硬件。UI 仅监听本机，不创建公共分享链接。

无需音频、Ollama 或模型下载的演示：

```powershell
python -m pip install -e .
python -m src.pipeline --demo --title "COMPxxxx — Neural Networks (Synthetic Demo)"
python -m unittest discover -s tests -v
```

演示使用合成转写、合成课件、词频向量和原文摘录，只检验管道及来源追溯；不能代表实际 ASR、语义对齐或 LLM 效果。

## Sources 与验证

### 仅课件模式

页面可以只上传 PDF/PPTX，无需录音。命令行也支持：

```powershell
.\.venv\Scripts\python.exe -m src.pipeline --slides "data/raw/slides/lecture.pptx" --title "课程课件笔记"
```

此模式需要 Ollama，按有文字的物理页逐页生成并核验笔记，不加载 Whisper 或 embedding 模型。Sources 仅含课件页码，没有音频时间或讲师讲解。空白页保留原始页号但跳过生成；全无文字的课件会提示需要 OCR 或录音。JSON 标记 `input_mode: slides_only`。

- 音频来源固定为 `audio:N`，携带原始 segment 起止秒数；同时保存 word timestamps。
- PDF / PPTX 使用 `slide:N` 和从 1 开始的物理页码，不依赖课件正文中的页号。
- 每条 claim 必须提供来源 ID 和原文 quote。校验器限制引用只能来自当前章节音频和候选课件，检查 quote 是否存在。
- 完整原文摘录通过确定性校验；改写内容再交给 Ollama 检查语义支持。失败的 claim 从 Markdown 剔除，理由保留在 JSON，完整草稿保留在 processed。
- Markdown 中的时间和页码从真实来源记录生成，不采信 LLM 生成的页码或时间。Sources 仅展示已接受 claim 使用的记录；相似课件匹配本身不是引用证据。
- 尚未校准准确率，Confidence 最高为 Medium；存在拒绝或无可用 claim 时为 Low。它不是正确概率。生成器与验证器使用同一模型，可能共同犯错。
- 暂使用确定性章节编号，避免未经验证的 LLM 章节标题引入事实。课程主标题由用户提供。

## 输出与模块

每次运行生成独立 ID，避免覆盖文件：

```text
config/config.yaml
data/raw/audio/                 原始音频
data/raw/slides/                原始课件
data/processed/<run-id>/
  transcripts/transcript.json   带时间戳转写
  slides/slides.json            逐页正文
  sections.json                 主题章节
  alignments/alignments.json    相似度候选
  drafts/                      核验前草稿
data/evaluation/                人工标注预留
src/audio/                     faster-whisper
src/documents/                 PyMuPDF4LLM / python-pptx
src/processing/                时长分块、相邻语义分段、余弦对齐
src/generation/                Pydantic、Ollama、Markdown
src/evaluation/                来源与语义校验、运行指标
src/pipeline.py                命令行与完整编排
app/gradio_app.py              本机上传与下载界面
outputs/notes/<run-id>/
  notes.md
  notes.json                   claim 引用、原文、设置、拒绝原因
  report.json                  接受比例、对齐覆盖率
```

复用已导出的转写：`python -m src.pipeline --transcript data/processed/<run-id>/transcripts/transcript.json --slides lecture.pptx`。CLI 使用 `--config` 读取 YAML；UI 采用 Settings 默认值。

分段合并相邻高相似度块，对齐选择超过阈值的 top-k 课件；没有匹配就保留音频证据，不强配。参数都是初始实验值，需用真实课程标注调参。分块不截断原始 segment，因此单个超长 segment 可超过时长上限；过长生成上下文显式报错，避免静默丢失证据。

## 第一版边界

PPTX 提取文本、表格和组合形状，不理解图片、图表或手写公式。PDF 使用逐页 Markdown，未加入视觉模型；扫描件效果取决于本地 OCR 能力。无文本页保留页码但不参与对齐。当前不做说话人分离、不播放定位音频、不做多课件文件合并。模型调用或解析失败会明确报错，不伪造结果；中间转写会在生成前保存。

实际音频与 Ollama 集成仍需在安装完整依赖、准备模型后验证。当前测试覆盖合成端到端链路、伪造来源、伪造引用、无证据推断、时间戳与拒绝匹配行为。报告指标不是 factual accuracy；模型对比、人工评价、可视化实验放到取得真实样本之后。

## 上游接口参考

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)：时间戳及 VAD。
- [PyMuPDF4LLM API](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/api.html)：逐页 Markdown。
- [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs)：JSON Schema 输出。
