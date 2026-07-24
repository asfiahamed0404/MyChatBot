# 📚 Asfi's NoteBot

Chat with PDF notes using retrieval-augmented generation (RAG). The Streamlit
app supports a free local mode and an optional paid OpenAI mode.

## Features

- Upload a text-based PDF and ask questions about its contents.
- Switch between free and paid modes from the sidebar.
- Review document page and chunk counts before starting a conversation.
- See the PDF pages retrieved for each answer.
- Start quickly with built-in topic, terminology, and quiz prompts.
- Keep chat history for the current Streamlit session.
- Build an in-memory FAISS index for document retrieval.
- Load API credentials from local Streamlit secrets or an environment variable.
- Keep local models cached between Streamlit reruns.
- Use a responsive dark interface with explicit document-processing controls.

## Modes

| Mode | Embeddings | Answer model | Data handling |
| --- | --- | --- | --- |
| Free | `sentence-transformers/all-MiniLM-L6-v2` | `Qwen2.5-1.5B-Instruct` (`Q4_K_M`) | Runs on the machine hosting the app after model download |
| Paid | `text-embedding-3-small` | `gpt-4o-mini` | Sends extracted PDF text for embedding and retrieved passages for answers |

Changing modes clears the current document index and indexes the uploaded PDF
again using the selected provider.

## Requirements

- Python 3.10 or newer; Python 3.11 is recommended and tested.
- `pip`
- Internet access during installation and the first free-model download.
- At least 2.5 GB of free disk space during the first download; about 1.2 GB
  remains cached afterward.
- 16 GB of system RAM is recommended for comfortable CPU free-mode use.
- An OpenAI API key only when using paid mode.

## Installation

Clone the repository:

```powershell
git clone https://github.com/asfiahamed0404/MyChatBot-OpenAIKEY-.git MyOwnChatBotProject
cd MyOwnChatBotProject
```

Create a virtual environment. On Windows, install the official prebuilt
`llama-cpp-python` CPU wheel first; this avoids needing a local C++ compiler:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu "llama-cpp-python==0.3.34"
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

For macOS or Linux:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt
```

On macOS or Linux, `llama-cpp-python` may compile locally and therefore needs a
C/C++ compiler and CMake. See the
[official installation options](https://github.com/abetlen/llama-cpp-python#installation)
for platform-specific CPU or Metal wheels.

## Configure paid mode

The free mode does not require an API key.

For paid mode, copy the provided example:

```powershell
Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
```

Then edit `.streamlit/secrets.toml` locally:

```toml
OPENAI_API_KEY = "replace-with-your-openai-api-key"
```

The real `.streamlit/secrets.toml` is ignored by Git. Never put a key directly
in Python code, commit it, or share it in screenshots or chat messages.

Alternatively, set an `OPENAI_API_KEY` environment variable before starting
the application.

## Run

Windows:

```powershell
.\.venv\Scripts\python.exe -m streamlit run .\asfi_notebot.py
```

macOS or Linux:

```bash
./.venv/bin/python -m streamlit run ./asfi_notebot.py
```

Open `http://localhost:8501` if Streamlit does not open it automatically.

This existing checkout also has a verified environment named `.venv_new`, so
it can be started with:

```powershell
.\.venv_new\Scripts\python.exe -m streamlit run .\asfi_notebot.py
```

## Usage

1. Select **Free** or **Paid** in the sidebar.
2. Upload a text-based PDF up to 25 MB and 300 pages.
3. Select **Prepare with local AI** or **Prepare with OpenAI**. Paid processing
   begins only after you press the button.
4. Wait for extraction, chunking, embedding, and indexing to finish.
5. Ask a question, or start with one of the suggested prompts.
6. Use **Clear chat** to reset messages or **Remove document** to remove the
   current in-memory index.

Scanned image-only PDFs require OCR before this application can extract their
text.

## Project structure

```text
MyOwnChatBotProject/
├── asfi_notebot.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
└── .streamlit/
    ├── config.toml
    └── secrets.toml.example
```

Local virtual environments, IDE settings, caches, and the real secrets file
are intentionally excluded from Git.

## Troubleshooting

Check the environment:

```powershell
.\.venv\Scripts\python.exe -m pip check
```

Reinstall declared dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If PowerShell blocks virtual-environment activation, use the full Python path
shown above; activation is optional.

The first free preparation downloads a pinned 4-bit Qwen model (about 1.1 GB)
plus the embedding model. The files stay in the normal Hugging Face cache
outside this repository and are reused later. CPU answers take longer than paid
API answers, but no PDF text or question is sent to OpenAI in free mode.

## Security

- Rotate a credential immediately if it is ever committed or shared.
- Removing a key from the latest file does not remove it from older Git commits.
- Review staged changes with `git diff --cached` before every push.
- Avoid `git add .` when unexpected untracked files are present.
- Before deploying paid mode publicly, add authentication, request limits, and
  a spending cap so visitors cannot consume a shared server API key.

## License

Licensed under the [MIT License](LICENSE).
