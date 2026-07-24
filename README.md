# Asfi's NoteBot

A page-aware PDF study assistant built with Streamlit. It supports:

- A free local mode using Qwen and FastEmbed, with no OpenAI calls.
- An optional paid local mode using OpenAI for stronger answers.
- A resource-bounded cloud profile using Cloudflare Workers AI Qwen3 for
  stronger free-demo answers.

## What it does

- Reads text-based PDFs and keeps page metadata with every passage.
- Retrieves the strongest passage plus nearby context from the same PDF page.
- Shows which PDF pages were used.
- Removes unsupported page citations and blocks remote images in model output.
- Keeps the document index and conversation in the current Streamlit session.
- Downloads pinned local models into the normal user cache, outside this repository.
- In the cloud profile, sends only the question and up to two retrieved passages
  to Cloudflare. The PDF file, filename, vector index, and chat history are not
  sent, but for a very short PDF those passages may contain most or all of its
  extracted text.

Scanned, image-only PDFs need OCR before NoteBot can read them.

## Modes

| Profile | Search model | Answer model | PDF handling |
| --- | --- | --- | --- |
| Local free | `BAAI/bge-small-en-v1.5` | `Qwen2.5-1.5B-Instruct` Q4 | Processed on your computer; not sent to OpenAI |
| Local paid | `text-embedding-3-small` | `gpt-4o-mini` | Extracted text and questions are sent to OpenAI |
| Free cloud | `BAAI/bge-small-en-v1.5` | Cloudflare Workers AI `Qwen3-30B-A3B-FP8` | PDF text is indexed in Streamlit memory; each question and up to two retrieved passages are sent to Cloudflare |

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

## Deploy on Streamlit Community Cloud

The repository contains a separate cloud entrypoint and does not install the
1.1 GB local Qwen answer model in the cloud build.

### 1. Create the Cloudflare credentials

1. Sign in to the [Cloudflare dashboard](https://dash.cloudflare.com/).
2. Open **Workers AI**, choose **Use REST API**, and use Cloudflare's
   **Create a Workers AI API Token** template.
3. Restrict the token to the one account used by this app. Do not use a Global
   API Key.
4. Copy the 32-character **Account ID** and the token, and store them securely.

Cloudflare's official [REST API guide](https://developers.cloudflare.com/workers-ai/get-started/rest-api/)
has the current dashboard steps and permission template.

### 2. Create or update the Streamlit app

1. Open [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Select **Create app**, then **Yup, I have an app**.
3. Use repository `asfiahamed0404/MyChatBot`.
4. Use branch `main`.
5. Use entrypoint `cloud/streamlit_app.py`.
6. Open **Advanced settings** and choose Python `3.11`.
7. Paste these values into **Secrets**, using the real values copied from
   Cloudflare:

   ```toml
   CLOUDFLARE_ACCOUNT_ID = "replace-with-your-32-character-account-id"
   CLOUDFLARE_API_TOKEN = "replace-with-your-workers-ai-api-token"
   ```

8. Do not add `OPENAI_API_KEY` to the public deployment.
9. Select **Deploy**. If the app already exists, save the secrets and reboot it.

The first PDF preparation downloads only the local search model (about 70 MB).
Community Cloud may hibernate inactive apps, so a cold start can still take
some time.

Free-cloud safeguards:

- Free mode only; no shared paid API key
- 10 MB, 100-page, 500,000-character, and 500-passage PDF limits
- Only two retrieved passages are sent per hosted answer
- 12 request attempts per browser session
- Best-effort per-app-process limits: two concurrent requests, 30 attempts per
  10 minutes, and 200 attempts per UTC day
- Session-memory document index

Cloudflare Workers AI currently includes 10,000 neurons per day on its Free
plan and returns an error after that allocation is used. If you later upgrade
the Cloudflare account to a paid Workers plan, usage beyond the included
allocation can become billable. Check the current
[Workers AI pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/)
before changing plans.

The in-app limits are per process and reset when Streamlit restarts or scales;
they are not authentication or durable denial-of-service protection. Use a
private deployment or add real authentication and persistent rate limiting
before sharing the app widely.

### Cloud privacy boundary

- PDF text is extracted, indexed, and held in the Streamlit server's session
  memory.
- For each answer, the question and up to two selected PDF passages go to
  Cloudflare Workers AI.
- The PDF file, filename, vector index, and previous messages are not included
  in the Cloudflare request. For a very short PDF, the selected passages may
  contain most or all of its extracted text.
- Cloudflare states that customer inputs and outputs are not used to train or
  improve its models without explicit consent. See its
  [Workers AI data-usage policy](https://developers.cloudflare.com/workers-ai/platform/data-usage/).

Do not upload confidential or sensitive material to a public demo.

## Use the app

1. Choose **Free** or **Paid** when running locally.
2. Upload a text-based PDF.
3. Select **Prepare with local AI**, **Prepare with OpenAI**, or
   **Prepare for hosted AI**, depending on the profile.
4. Wait for extraction, embedding, and indexing.
5. Ask a specific question, such as `What is a parametric curve?`
6. Check the retrieved page number shown under the answer.

Local limits are 25 MB and 300 pages.

## Project structure

```text
MyOwnChatBotProject/
|-- asfi_notebot.py
|-- answer_safety.py
|-- cloudflare_ai.py
|-- requirements.txt
|-- README.md
|-- LICENSE
|-- .gitignore
|-- .streamlit/
|   |-- config.toml
|   `-- secrets.toml.example
|-- tests/
|   |-- test_answer_safety.py
|   `-- test_cloudflare_ai.py
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

For a cloud `401` or `403` error, recreate the token with Cloudflare's Workers
AI template and confirm that it is restricted to the same account ID. A `429`
usually means the free daily allocation or a request limit has been reached.

## Security

- Rotate a credential immediately if it is committed or shared.
- Removing a key from the latest file does not remove it from older Git commits.
- Review staged changes with `git diff --cached` before every push.
- Keep `.streamlit/secrets.toml` local and ignored.
- Keep Cloudflare credentials only in environment variables or Streamlit
  Secrets; never put them in Python or browser/session state.
- Do not enable paid mode in a public app without authentication, rate limits,
  and an OpenAI spending cap.

## License

Licensed under the [MIT License](LICENSE).
