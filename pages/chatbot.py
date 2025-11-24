# pages/chatbot.py  (only changes: import + llm lines)
import streamlit as st
import pandas as pd
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI  # For Grok compatibility

# -------------------------- Caching --------------------------
@st.cache_resource(show_spinner="Loading AI model and vector index (first time only)...")
def load_rag_chain():
    df = pd.read_csv("Incident_Details.csv")   # Ensure CSV is committed to GitHub

    # Create rich text chunks (unchanged)
    texts = []
    metadatas = []
    for _, row in df.iterrows():
        text = f"""Incident {row['INC#']} | Priority {row['Priority']} | Product {row['Product']}
Date: {row['Date']} | Duration: {row['Duration(min)']} minutes
Causation: {row['Initial Causation']} → {row['Final Causation']}
Code: {row['Causation Code']}
Comments: {row.get('Comments', 'None')}
Repeat: {row['Repeat']}"""
        texts.append(text)
        metadatas.append({"inc": row['INC#'], "product": row['Product'], "date": row['Date']})

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 6})

    template = """You are an expert incident analyst. Answer ONLY using the context below.
If you are not sure, say "I don't have enough information".

Context:
{context}

Question: {question}
Answer:"""

    prompt = ChatPromptTemplate.from_template(template)

    # Cloud-ready: Grok via OpenAI-compatible API (free tier)
    llm = ChatOpenAI(
        base_url="https://api.x.ai/v1",
        api_key=st.secrets["API_KEY"],  # Pulled from Streamlit secrets
        model="grok-3",  # Or "grok-2-latest" for even better results
        temperature=0
    )

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain, retriever

rag_chain, retriever = load_rag_chain()

# -------------------------- UI (unchanged) --------------------------
st.title("Incident Chatbot")
st.caption("Powered by Grok + your CSV — production-ready & private")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("Ask anything about the incidents..."):
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
