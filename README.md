# 📚 Asfi's NoteBot

Chat with PDF notes using retrieval-augmented generation (RAG). The Streamlit
app supports a free local mode and an optional paid OpenAI mode.

## Features

- Upload a text-based PDF and ask questions about its contents.
- Switch between free and paid modes from the sidebar.
- Keep chat history for the current Streamlit session.
- Build an in-memory FAISS index for document retrieval.
- Load API credentials from local Streamlit secrets or an environment variable.
- Keep local models cached between Streamlit reruns.

## Modes

| Mode | Embeddings | Answer model | Data handling |
| --- | --- | --- | --- |
| Free | `sentence-transformers/all-MiniLM-L6-v2` | `google/flan-t5-small` | Runs locally after model download |
| Paid | `text-embedding-3-small` | `gpt-4o-mini` | Sends relevant document text to OpenAI |

Changing modes clears the current document index and indexes the uploaded PDF
again using the selected provider.

## Requirements

- Python 3.10 or newer; Python 3.11 is recommended and tested.
- `pip`
- Internet access during installation and the first free-model download.
- An OpenAI API key only when using paid mode.

## Installation

Clone the repository:

```powershell
git clone https://github.com/asfiahamed0404/MyChatBot-OpenAIKEY-.git MyOwnChatBotProject
cd MyOwnChatBotProject
```

Create a virtual environment and install the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

For macOS or Linux:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt
```

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
2. Upload a text-based PDF.
3. Wait for extraction, chunking, embedding, and indexing to finish.
4. Ask questions in the chat box.
5. Use **Reset Chat** to clear messages or **Clear Document** to remove the
   current index.

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

The first use of free mode downloads the Hugging Face models and can take
longer than later runs. CPU inference is supported but may be slow.

## Security

- Rotate a credential immediately if it is ever committed or shared.
- Removing a key from the latest file does not remove it from older Git commits.
- Review staged changes with `git diff --cached` before every push.
- Avoid `git add .` when unexpected untracked files are present.

## License

Licensed under the [MIT License](LICENSE).
