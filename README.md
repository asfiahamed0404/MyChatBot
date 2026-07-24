# Asfi's NoteBot

A page-aware PDF study assistant built with Streamlit. It supports:

- A free local mode using Qwen and FastEmbed, with no OpenAI calls.
- An optional paid local mode using OpenAI for stronger answers.
- A resource-bounded free profile prepared for Streamlit Community Cloud.

## What it does

- Reads text-based PDFs and keeps page metadata with every passage.
- Retrieves the strongest passage plus nearby context from the same PDF page.
- Shows which PDF pages were used.
- Removes unsupported page citations and blocks remote images in model output.
- Keeps the document index and conversation in the current Streamlit session.
- Downloads pinned local models into the normal user cache, outside this repository.

Scanned, image-only PDFs need OCR before NoteBot can read them.

## Modes

| Profile | Search model | Answer model | PDF handling |
| --- | --- | --- | --- |
| Local free | `BAAI/bge-small-en-v1.5` | `Qwen2.5-1.5B-Instruct` Q4 | Processed on your computer; not sent to OpenAI |
| Local paid | `text-embedding-3-small` | `gpt-4o-mini` | Extracted text and questions are sent to OpenAI |
| Free cloud | `BAAI/bge-small-en-v1.5` | `Qwen2.5-1.5B-Instruct` Q4 | Processed in Streamlit's hosted memory; not sent to OpenAI |

The public cloud entrypoint intentionally disables paid mode. This prevents
visitors from spending money through a shared OpenAI key.

## Run locally

Requirements:

- Python 3.11 recommended
- Internet access during installation and the first model download
- About 2.5 GB free disk space
- 16 GB RAM recommended for comfortable local free-mode use
- An OpenAI API key only for paid mode

Clone and enter the project:

```powershell
git clone https://github.com/asfiahamed0404/MyChatBot.git MyOwnChatBotProject
cd MyOwnChatBotProject
```

On Windows, create an environment and install the prebuilt CPU wheel first:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu "llama-cpp-python==0.3.34"
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run .\asfi_notebot.py
```

On macOS or Linux:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m streamlit run ./asfi_notebot.py
```

`llama-cpp-python` may compile on macOS or Linux if a compatible wheel is not
available, which requires a C/C++ compiler and CMake.

Open `http://localhost:8501` if Streamlit does not open automatically.

### Configure local paid mode

Free mode does not need an API key. For paid mode:

```powershell
Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
```

Then edit the ignored `.streamlit/secrets.toml` file:

```toml
OPENAI_API_KEY = "replace-with-your-new-openai-api-key"
```

You can instead set the `OPENAI_API_KEY` environment variable before starting
Streamlit. Never put the key in Python, commit it, or paste it into a public
deployment file.

## Deploy free on Streamlit Community Cloud

The repository contains a separate cloud entrypoint and a small dependency set.
The only remaining deployment action needs your GitHub/Streamlit login:

1. Open [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Select **Create app**, then **Yup, I have an app**.
3. Use repository `asfiahamed0404/MyChatBot`.
4. Use branch `main`.
5. Use entrypoint `cloud/streamlit_app.py`.
6. Open **Advanced settings** and choose Python `3.11`.
7. Leave **Secrets** empty; the free cloud profile does not use an API key.
8. Select **Deploy**.

The first preparation downloads about 1.2 GB of models and can take several
minutes. Community Cloud may hibernate inactive apps, so a cold start can also
take time.

Free-cloud safeguards:

- Free mode only; no shared paid API key
- 10 MB, 100-page, 500,000-character, and 500-passage PDF limits
- 12 successful answers per browser session as a soft usage cap
- Two CPU inference threads and serialized model use
- Session-memory document index

Community Cloud resource limits and availability can change. If the app reaches
a hosting limit, check its cloud logs and reboot it from **Manage app**.
The session cap prevents accidental overuse, but it is not authentication or
strong denial-of-service protection. Use a private deployment or add real
authentication before relying on the app for controlled access.

## Use the app

1. Choose **Free** or **Paid** when running locally.
2. Upload a text-based PDF.
3. Select **Prepare with local AI** or **Prepare with OpenAI**.
4. Wait for extraction, embedding, and indexing.
5. Ask a specific question, such as `What is a parametric curve?`
6. Check the retrieved page number shown under the answer.

Local limits are 25 MB and 300 pages.

## Project structure

```text
MyOwnChatBotProject/
|-- asfi_notebot.py
|-- requirements.txt
|-- README.md
|-- LICENSE
|-- .gitignore
|-- .streamlit/
|   |-- config.toml
|   `-- secrets.toml.example
`-- cloud/
    |-- streamlit_app.py
    `-- requirements.txt
```

Virtual environments, IDE settings, logs, model weights, and the real secrets
file are excluded from Git.

## Troubleshooting

Check the local environment:

```powershell
.\.venv\Scripts\python.exe -m pip check
```

If free preparation fails on first use, verify internet access and free disk
space, then restart Streamlit. If an answer is weak, ask a more specific
question and confirm that the displayed retrieved pages contain the topic.

## Security

- Rotate a credential immediately if it is committed or shared.
- Removing a key from the latest file does not remove it from older Git commits.
- Review staged changes with `git diff --cached` before every push.
- Keep `.streamlit/secrets.toml` local and ignored.
- Do not enable paid mode in a public app without authentication, rate limits,
  and an OpenAI spending cap.

## License

Licensed under the [MIT License](LICENSE).
