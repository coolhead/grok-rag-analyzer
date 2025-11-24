# pages/chatbot.py  ← FINAL VERSION: AUTO TODAY'S DATE + FOREVER ACCURATE
import streamlit as st
import pandas as pd
from datetime import datetime
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

st.set_page_config(page_title="Incident Chatbot", layout="centered")

st.title("Incident Chatbot (Any CSV)")
st.caption("Drop any incident CSV → ask questions in plain English. Powered by Grok 4.1")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if not uploaded_file:
    st.info("Please upload a CSV file to begin")
    st.stop()

@st.cache_resource(show_spinner="Building AI index from your CSV...")
def build_rag_chain(df):
    texts = []
    metadatas = []
    for _, row in df.iterrows():
        text = f"""Incident {row.get('INC#', 'N/A')} | Priority {row.get('Priority', 'N/A')} | Product {row.get('Product', 'N/A')}
Date: {row.get('Date', 'N/A')} | Duration: {row.get('Duration(min)', 'N/A')} min
Causation: {row.get('Initial Causation', 'N/A')} → {row.get('Final Causation', 'N/A')}
Code: {row.get('Causation Code', 'N/A')} | Comments: {row.get('Comments', 'None')}
Repeat: {row.get('Repeat', 'No')}"""
        texts.append(text)
        metadatas.append({"inc": str(row.get('INC#', ''))})

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 8})  # increased for better date coverage

    # AUTO TODAY'S DATE — NO HARDCODING!
    today = datetime.now().strftime("%B %d, %Y")

    template = f"""You are an expert incident analyst.
Today's date is {today}. Use this to interpret "last 30 days", "this month", "last year", etc.

Answer using ONLY the context below. If the question involves dates and you cannot confidently calculate it from the context, say "I don't have enough information".

Context:
{{context}}

Question: {{question}}
Answer:"""

    prompt = ChatPromptTemplate.from_template(template)

    llm = ChatOpenAI(
        base_url="https://api.x.ai/v1",
        api_key=st.secrets["API_KEY"],
        model="grok-4-1-fast-reasoning",
        temperature=0
    )

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain, retriever

# Load CSV
df = pd.read_csv(uploaded_file)
st.success(f"Loaded {len(df):,} rows from {uploaded_file.name}")

rag_chain, retriever = build_rag_chain(df)

# Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("Ask anything about this CSV..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Grok is thinking..."):
            response = rag_chain.invoke(prompt)
        st.write(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

    with st.expander("View sources"):
        docs = retriever.invoke(prompt)
        for i, doc in enumerate(docs, 1):
            st.caption(f"Source {i} → INC {doc.metadata.get('inc')}")
            st.code(doc.page_content[:600], language="text")
