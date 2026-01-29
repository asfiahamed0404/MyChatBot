import streamlit as st
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import HuggingFaceHub
from langchain_core.language_models.llms import LLM
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from typing import Optional, List, Any
import torch

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="NoteBot Intelligence",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR MODERN UI ---
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Gradient Background */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    }
    
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Glassmorphism Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        background: transparent !important;
    }
    
    /* Chat message styling */
    [data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(5px) !important;
        border-radius: 15px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 1rem !important;
        margin-bottom: 1rem !important;
    }
    
    /* Chat input styling */
    [data-testid="stChatInput"] {
        background: rgba(255, 255, 255, 0.08) !important;
        border-radius: 25px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    
    [data-testid="stChatInput"] input {
        color: white !important;
    }
    
    /* File uploader styling */
    [data-testid="stFileUploader"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 15px !important;
        padding: 1rem !important;
        border: 1px dashed rgba(255, 255, 255, 0.3) !important;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 0.5rem 2rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4) !important;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #ffffff !important;
    }
    
    /* Text color */
    p, span, label {
        color: rgba(255, 255, 255, 0.85) !important;
    }
    
    /* Success/Info/Warning boxes */
    .stAlert {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Divider */
    hr {
        border-color: rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Logo header */
    .logo-header {
        display: flex;
        align-items: center;
        gap: 15px;
        padding: 1rem 0;
    }
    
    .logo-emoji {
        font-size: 3rem;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .app-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .app-subtitle {
        font-size: 1rem;
        color: rgba(255, 255, 255, 0.6) !important;
        font-weight: 300;
    }
</style>
""", unsafe_allow_html=True)

# --- INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "current_file" not in st.session_state:
    st.session_state.current_file = None

# --- HEADER WITH LOGO ---
col1, col2 = st.columns([1, 10])
with col1:
    st.markdown('<span style="font-size: 4rem;">📚</span>', unsafe_allow_html=True)
with col2:
    st.markdown('<p class="app-title">NoteBot Intelligence</p>', unsafe_allow_html=True)
    st.markdown('<p class="app-subtitle">Your AI-powered study companion • Upload PDFs and chat with your notes</p>', unsafe_allow_html=True)

st.divider()

# --- FREE MODE TOGGLE ---
# Set to True to use FREE HuggingFace models (no API costs)
# Set to False to use OpenAI API (better quality, costs money)
FREE_MODE = True
#FREE_MODE = False


# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Mode")
    if FREE_MODE:
        st.success("🆓 FREE MODE - Using HuggingFace")
        st.caption("No API costs • Local models")
    else:
        st.warning("💰 PAID MODE - Using OpenAI")
        st.caption("Better quality • Costs tokens")
    
    st.divider()
    
    st.markdown("### 📁 Upload Notes")
    file = st.file_uploader(
        "Drop your PDF here",
        type="pdf",
        help="Upload a lecture PDF to start chatting with your notes"
    )
    
    st.divider()
    
    # Reset Chat Button
    if st.button("🔄 Reset Chat", use_container_width=True):
        st.session_state.messages = []
        st.toast("Chat cleared!", icon="✨")
        st.rerun()
    
    # Clear Vector Store Button
    if st.button("🗑️ Clear Document", use_container_width=True):
        st.session_state.vector_store = None
        st.session_state.current_file = None
        st.session_state.messages = []
        st.toast("Document cleared!", icon="🗑️")
        st.rerun()
    
    st.divider()
    
    # Status indicator
    if st.session_state.vector_store:
        st.success(f"📄 **{st.session_state.current_file}** loaded")
    else:
        st.info("👆 Upload a PDF to get started")
    
    st.divider()
    st.markdown("---")
    if FREE_MODE:
        st.markdown(
            '<p style="text-align: center; font-size: 0.8rem; opacity: 0.5;">Powered by HuggingFace & LangChain</p>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<p style="text-align: center; font-size: 0.8rem; opacity: 0.5;">Powered by OpenAI & LangChain</p>',
            unsafe_allow_html=True
        )

# --- HELPER FUNCTION: Get API Key ---
def get_api_key():
    """Retrieve OpenAI API key from Streamlit secrets"""
    try:
        return st.secrets["OPENAI_API_KEY"]
    except KeyError:
        st.error("""
        ⚠️ **OpenAI API Key not found!**
        
        Please set up your API key:
        1. Create a folder `.streamlit` in your project root
        2. Create a file `secrets.toml` inside it
        3. Add: `OPENAI_API_KEY = "your-api-key-here"`
        """)
        st.stop()

# --- FREE LLM: FLAN-T5 (runs locally, no API costs) ---
class FlanT5LLM(LLM):
    """Free local LLM using FLAN-T5"""
    model_name: str = "google/flan-t5-small"
    tokenizer: Any = None
    model: Any = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name).to(device)
    
    @property
    def _llm_type(self) -> str:
        return "flan-t5"
    
    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs) -> str:
        device = self.model.device
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(device)
        outputs = self.model.generate(**inputs, max_new_tokens=256, do_sample=False)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

@st.cache_resource
def get_free_llm():
    """Cached FLAN-T5 model to avoid reloading"""
    return FlanT5LLM()

# --- PROCESS PDF ---
if file is not None:
    # Check if this is a new file
    if st.session_state.current_file != file.name:
        with st.status("🔄 Processing your document...", expanded=True) as status:
            try:
                # Step 1: Extract text
                st.write("📖 Extracting text from PDF...")
                pdf_reader = PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() or ""
                
                if not text.strip():
                    st.error("Could not extract text from PDF. Please try another file.")
                    st.stop()
                
                # Step 2: Split into chunks
                st.write("✂️ Splitting into chunks...")
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=500,
                    chunk_overlap=100,
                    length_function=len
                )
                chunks = splitter.split_text(text)
                st.write(f"   Created {len(chunks)} chunks")
                
                # Step 3: Create embeddings
                st.write("🧠 Creating embeddings...")
                if FREE_MODE:
                    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
                else:
                    from langchain_openai import OpenAIEmbeddings
                    api_key = get_api_key()
                    embeddings = OpenAIEmbeddings(api_key=api_key)
                
                # Step 4: Build vector store
                st.write("📊 Building vector database...")
                st.session_state.vector_store = FAISS.from_texts(chunks, embeddings)
                st.session_state.current_file = file.name
                
                status.update(label="✅ Document ready!", state="complete", expanded=False)
                st.toast("Document indexed successfully!", icon="🎉")
                
            except Exception as e:
                st.error(f"Error processing PDF: {e}")
                st.stop()

# --- CHAT INTERFACE ---
if st.session_state.vector_store:
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="🧑‍🎓" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your notes..."):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user", avatar="🧑‍🎓"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking..."):
                try:
                    # Retrieve relevant chunks
                    docs = st.session_state.vector_store.similarity_search(prompt, k=4)
                    context = "\n\n".join([doc.page_content for doc in docs])
                    
                    # Initialize LLM based on mode
                    if FREE_MODE:
                        llm = get_free_llm()
                        # Simpler prompt for FLAN-T5
                        chat_prompt = ChatPromptTemplate.from_template("""Answer the question based on this context:

Context: {context}

Question: {question}

Answer:""")
                    else:
                        from langchain_openai import ChatOpenAI
                        api_key = get_api_key()
                        llm = ChatOpenAI(
                            api_key=api_key,
                            model="gpt-3.5-turbo",
                            temperature=0.2,
                            max_tokens=500
                        )
                        # Detailed prompt for OpenAI
                        chat_prompt = ChatPromptTemplate.from_template("""
You are NoteBot, an intelligent study assistant. Answer the question based on the provided context from the user's notes.

Guidelines:
- Be helpful, clear, and concise
- Use bullet points for lists
- If the answer isn't in the context, say "I couldn't find that in your notes"
- Highlight key terms when relevant

Context from notes:
{context}

Question: {question}

Answer:""")
                    
                    # Generate response
                    chain = chat_prompt | llm | StrOutputParser()
                    response = chain.invoke({
                        "context": context,
                        "question": prompt
                    })
                    
                    st.markdown(response)
                    
                    # Add assistant message to history
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    st.error(f"Error generating response: {e}")

else:
    # Welcome message when no document is loaded
    st.markdown("""
    <div style="
        text-align: center;
        padding: 4rem 2rem;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-top: 2rem;
    ">
        <h2 style="font-size: 3rem; margin-bottom: 1rem;">👋 Welcome to NoteBot!</h2>
        <p style="font-size: 1.2rem; opacity: 0.7; margin-bottom: 2rem;">
            Upload a PDF in the sidebar to start chatting with your notes
        </p>
        <div style="display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap;">
            <div style="text-align: center;">
                <span style="font-size: 2rem;">📄</span>
                <p style="font-size: 0.9rem; opacity: 0.6;">Upload PDF</p>
            </div>
            <div style="text-align: center;">
                <span style="font-size: 2rem;">🔍</span>
                <p style="font-size: 0.9rem; opacity: 0.6;">AI Indexing</p>
            </div>
            <div style="text-align: center;">
                <span style="font-size: 2rem;">💬</span>
                <p style="font-size: 0.9rem; opacity: 0.6;">Chat Away!</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)