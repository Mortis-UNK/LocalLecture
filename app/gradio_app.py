import os

from src.pipeline import load_settings, run


def configure_local_proxy_bypass():
    """Keep external proxies, but connect directly to this app's loopback server."""
    entries = []
    for key in ("NO_PROXY", "no_proxy"):
        entries.extend(value.strip() for value in os.environ.get(key, "").split(",") if value.strip())
    entries.extend(["localhost", "127.0.0.1", "::1"])
    bypass = ",".join(dict.fromkeys(entries))
    os.environ["NO_PROXY"] = bypass
    os.environ["no_proxy"] = bypass


def build_app():
    configure_local_proxy_bypass()
    import gradio as gr

    def generate(audio, slides, title, demo):
        try:
            markdown, md, structured = run(audio=audio, slides_path=slides, title=title,
                                         demo=demo, settings=load_settings())
            return markdown, md, structured
        except Exception as exc:
            raise gr.Error(str(exc)) from exc

    with gr.Blocks(title="LocalLecture") as ui:
        gr.Markdown("# LocalLecture\n把课堂录音与课件整理为可追溯笔记。Sources 保留时间段和页码。")
        gr.Markdown("支持仅录音、仅课件，或录音搭配课件。仅课件模式按页整理，来源只含页码；需要启动 Ollama。")
        title = gr.Textbox(label="课程标题", value="Lecture Notes")
        audio = gr.Audio(type="filepath", label="课堂录音（仅课件模式可不上传）")
        slides = gr.File(file_types=[".pdf", ".pptx"], type="filepath", label="课件（可选）")
        demo = gr.Checkbox(label="合成演示（忽略上传文件，不调用模型）", value=False)
        button = gr.Button("生成笔记", variant="primary")
        notes = gr.Markdown()
        md = gr.File(label="下载 Markdown")
        structured = gr.File(label="下载 JSON 与证据记录")
        button.click(generate, [audio, slides, title, demo], [notes, md, structured], concurrency_limit=1)
    return ui


def main():
    build_app().queue().launch(server_name="127.0.0.1", share=False)


if __name__ == "__main__":
    main()
