import streamlit as st

st.header("NoteBot")

with st.sidebar:
    st.title("My Notes")
    file = st.file_uploader("Upload notes PDF and start asking questions", type="pdf")