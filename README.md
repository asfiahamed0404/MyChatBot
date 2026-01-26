# **NoteBot – Retrieval-Augmented Generation (RAG) PDF Chatbot**

## **Project Description**

NoteBot is a Retrieval-Augmented Generation (RAG) based question-answering system that enables users to interact with PDF documents through natural language queries. The application is designed to help students, educators, and professionals efficiently extract information from large documents such as lecture notes, textbooks, and research papers.

The system processes uploaded PDF files by extracting their text content and dividing it into overlapping chunks to preserve contextual meaning. These chunks are transformed into vector embeddings using OpenAI or HuggingFace embedding models and stored in a FAISS vector database to support fast and accurate semantic retrieval.

When a user submits a question, NoteBot performs a similarity search over the vector database to retrieve the most relevant document segments. These retrieved chunks are then provided to a large language model (GPT-3.5-turbo) through a carefully designed prompt, enabling the model to generate context-aware and grounded responses. If the required information is not present in the retrieved context, the system explicitly responds with “I don’t know,” reducing hallucinations and improving answer reliability.

This project demonstrates a complete end-to-end implementation of the RAG architecture by combining document retrieval, vector search, and large language models within an intuitive Streamlit interface.

---

## **Key Highlights**

- End-to-end RAG pipeline implementation  
- PDF ingestion and intelligent text chunking  
- Semantic search using vector embeddings and FAISS  
- Context-aware answer generation with GPT-3.5  
- Hallucination control via prompt engineering  
- User-friendly web interface built with Streamlit  

---

## **Tech Stack**

- **Language**: Python  
- **Frontend**: Streamlit  
- **LLM**: OpenAI GPT-3.5-turbo  
- **Framework**: LangChain  
- **Embeddings**: OpenAI  
- **Vector Store**: FAISS  
- **PDF Processing**: PyPDF2  
