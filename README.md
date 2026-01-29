# 📚 NoteBot Intelligence

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-Latest-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Your AI-Powered Study Companion** 🤖

*Upload PDFs and chat with your notes using RAG (Retrieval-Augmented Generation)*

[Features](#-features) • [Demo](#-demo) • [Installation](#-installation) • [Usage](#-usage) • [Configuration](#-configuration)

</div>

---

## 🎯 Overview

**NoteBot Intelligence** is a modern, production-ready RAG (Retrieval-Augmented Generation) chatbot that allows you to have intelligent conversations with your PDF documents. Built with a stunning glassmorphism UI, it supports both **FREE** (HuggingFace) and **PAID** (OpenAI) modes.

Perfect for:
- 📖 Students studying lecture notes
- 📚 Researchers analyzing papers
- 💼 Professionals reviewing documents
- 🎓 Educators creating study materials

---

## ✨ Features

### 🎨 Modern UI/UX
- **Glassmorphism Design** - Beautiful frosted glass effect sidebar
- **Gradient Background** - Deep blue to purple gradient
- **Custom Fonts** - Google Inter font for a SaaS look
- **Responsive Layout** - Works on desktop and tablet

### 💬 Chat Interface
- **Native Chat UI** - Modern messaging app experience with `st.chat_message`
- **Chat History** - Persistent conversation across interactions
- **User/Bot Avatars** - Visual distinction between messages

### 🔄 Dual Mode Support
| Mode | Embeddings | LLM | Cost |
|------|------------|-----|------|
| 🆓 **FREE** | HuggingFace (MiniLM) | FLAN-T5 (Local) | **$0** |
| 💰 **PAID** | OpenAI | GPT-3.5-turbo | Pay per use |

### 🔐 Security
- **No Hardcoded Keys** - API keys stored in `.streamlit/secrets.toml`
- **Secure Configuration** - Following Streamlit best practices

### ⚡ Performance
- **Cached Models** - `@st.cache_resource` for fast reloads
- **FAISS Vector Store** - Lightning-fast similarity search
- **Chunked Processing** - Efficient memory usage

---

## 🎬 Demo

```
┌─────────────────────────────────────────────────────────────┐
│  📚 NoteBot Intelligence                                    │
│  Your AI-powered study companion                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🧑‍🎓 User: What are the main topics in chapter 3?    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🤖 NoteBot: Based on your notes, chapter 3 covers: │   │
│  │   • Machine Learning fundamentals                   │   │
│  │   • Supervised vs Unsupervised learning            │   │
│  │   • Neural network architectures                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 💬 Ask a question about your notes...              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager
- (Optional) CUDA-compatible GPU for faster inference

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/NoteBot-Intelligence.git
cd NoteBot-Intelligence
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install streamlit PyPDF2 langchain langchain-community langchain-core langchain-openai langchain-text-splitters faiss-cpu sentence-transformers transformers torch
```

### 4. Set Up Secrets (for PAID mode)

Create the secrets file:

```bash
mkdir .streamlit
```

Create `.streamlit/secrets.toml`:

```toml
# OpenAI API Key (only needed for PAID mode)
OPENAI_API_KEY = "sk-your-api-key-here"
```

> ⚠️ **Important**: Add `.streamlit/secrets.toml` to your `.gitignore` to keep your API key safe!

---

## 📖 Usage

### Run the App

```bash
streamlit run MyChatBot.py
```

The app will open at `http://localhost:8501`

### Switch Between Modes

Edit line 168 in `MyChatBot.py`:

```python
# FREE mode (no API costs)
FREE_MODE = True

# PAID mode (uses OpenAI API)
FREE_MODE = False
```

### Using the App

1. **Upload PDF** - Drag and drop or click to upload in the sidebar
2. **Wait for Processing** - Watch the status indicator as it:
   - 📖 Extracts text
   - ✂️ Splits into chunks
   - 🧠 Creates embeddings
   - 📊 Builds vector database
3. **Start Chatting** - Ask questions about your document!
4. **Reset/Clear** - Use sidebar buttons to reset chat or clear document

---

## ⚙️ Configuration

### Mode Comparison

| Feature | FREE Mode | PAID Mode |
|---------|-----------|-----------|
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 | OpenAI text-embedding-ada-002 |
| **LLM** | google/flan-t5-small (local) | gpt-3.5-turbo |
| **Quality** | Good | Excellent |
| **Speed** | Depends on hardware | Fast (cloud) |
| **Cost** | Free | ~$0.002 per 1K tokens |
| **Privacy** | Data stays local | Data sent to OpenAI |
| **First Run** | Downloads ~300MB model | Instant |

### Customization

#### Change Chunk Size
```python
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,      # Adjust based on your needs
    chunk_overlap=100,   # Overlap for context continuity
    length_function=len
)
```

#### Change LLM Model (PAID mode)
```python
llm = ChatOpenAI(
    model="gpt-4",           # Use GPT-4 for better quality
    temperature=0.2,         # Lower = more focused
    max_tokens=500           # Limit response length
)
```

#### Change Embedding Model (FREE mode)
```python
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2"  # Better quality
)
```

---

## 📁 Project Structure

```
NoteBot-Intelligence/
├── MyChatBot.py           # Main application
├── gemini.py              # Alternative implementation
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── .gitignore             # Git ignore rules
└── .streamlit/
    └── secrets.toml       # API keys (not in git)
```

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| **Frontend** | Streamlit |
| **Backend** | Python 3.9+ |
| **LLM Framework** | LangChain |
| **Vector Store** | FAISS |
| **Embeddings (Free)** | HuggingFace Sentence Transformers |
| **Embeddings (Paid)** | OpenAI |
| **LLM (Free)** | Google FLAN-T5 |
| **LLM (Paid)** | OpenAI GPT-3.5-turbo |
| **PDF Processing** | PyPDF2 |

---

## 🔧 Troubleshooting

### Common Issues

**1. Module Not Found Error**
```bash
pip install --upgrade langchain langchain-community langchain-core
```

**2. CUDA/GPU Issues (FREE mode)**
```bash
# CPU-only installation
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

**3. OpenAI API Error**
- Check your API key in `.streamlit/secrets.toml`
- Ensure you have credits in your OpenAI account
- Verify the key format: `OPENAI_API_KEY = "sk-..."`

**4. PDF Text Extraction Issues**
- Ensure PDF is not scanned (image-based)
- Try a different PDF
- Some encrypted PDFs may not work

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Streamlit](https://streamlit.io/) - Amazing web app framework
- [LangChain](https://langchain.com/) - LLM application framework
- [HuggingFace](https://huggingface.co/) - Open-source ML models
- [OpenAI](https://openai.com/) - GPT models
- [FAISS](https://github.com/facebookresearch/faiss) - Vector similarity search

---

<div align="center">

**Made with ❤️ for learners everywhere**

⭐ Star this repo if you find it helpful!

</div>
