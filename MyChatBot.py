import streamlit as st
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

OpenAI_API_KEY = "REMOVED_REVOKED_OPENAI_API_KEY"

st.header("NoteBot")

with st.sidebar:
    st.title("My Notes")
    file = st.file_uploader("Upload notes PDF and start asking questions", type="pdf")

#extracting the text from pdf file
if file is not None:
    my_pdf=PdfReader(file)
    text=" "
    for page in my_pdf.pages:
        text += page.extract_text()
    st.write(text)

    #break into Chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    chunks = splitter.split_text(text)
    #st.write(chunks)

    embeddings = OpenAIEmbeddings(api_key=OpenAI_API_KEY)

    vector_store = FAISS.from_texts(chunks, embeddings)