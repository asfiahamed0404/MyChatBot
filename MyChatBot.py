import streamlit as st
from PyPDF2 import PdfReader

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