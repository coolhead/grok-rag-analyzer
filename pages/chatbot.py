# pages/chatbot.py  ← FINAL PRODUCTION VERSION WITH CSV UPLOAD
import streamlit as st
import pandas as pd
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

# -------------------------- Title & Uploader --------------------------
st.title("Incident Chatbot (Any CSV)")
st.caption("Drop any incident CSV below → get instant AI answers")

uploaded_file = st.file_uploader("Upload your incident CSV file", type=["csv"])

if not uploaded_file:
    st.info("Please upload a CSV file to start chatting")
    st.stop()

# -------------------------- Load & Index the CSV --------------------------
@st.cache_resource(show_spinner="Analyzing your CSV and building AI index...")
def build_rag_chain(df: pd.DataFrame):
    # Create rich text chunks
    texts = []
    metadatas = []
    for _, row in df.iterrows():
        # Make it robust — handle missing columns gracefully
        text = f"""Incident {row.get('INC#', 'Unknown')} | Priority {row.get('Priority', 'N/A')} | Product {row.get('Product', 'N/A')}
Date: {row.get('Date', 'Unknown')} | Duration: {row.get('Duration(min)', 'N/A')} min
Causation: {row.get('Initial Causation', 'N/A')} → {row.get('Final Causation', 'N/A')}
Code: {row.get('Causation Code', 'N/A')}
Comments: {row.get('Comments', 'None')}
Repeat: {row.get('Repeat', 'No')}"""
        texts.append(text)
        metadatas.append({
            "inc": str(row.get('INC#', '')),
            "product": str(row.get('Product', '')),
            "date": str(row.get('Date', ''))
        })

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 6})

    template = """You are an expert incident analyst. Answer using ONLY the context below.
If unsure, say "I don't have enough information".

Context:
{context}

Question: {question}
Answer:"""

    prompt = ChatPromptTemplate.from_template(template)

    llm = ChatOpenAI(
        base_url="https://api.x.ai/v1",
        api_key=st.secrets["API_KEY"],   # ← matches your existing secret name
        model="grok-beta",
        temperature=0
    )

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain, retriever

# Load the uploaded CSV
df = pd.read_csv(uploaded_file)
st.success(f"Loaded {len(df)} incidents from {uploaded_file.name}")

rag_chain, retriever = build_rag_chain(df)

# -------------------------- Chat UI --------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("Ask anything about this CSV..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = rag_chain.invoke(prompt)
        st.write(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

    with st.expander("View retrieved sources"):
        docs = retriever.invoke(prompt)
        for i, doc in enumerate(docs, 1):
            st.caption(f"Source {i} – INC {doc.metadata.get('inc')}")
            st.code(doc.page_content[:600], language="text")
