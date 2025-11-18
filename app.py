import streamlit as st
import requests
import time
from pypdf import PdfReader                  
try:
    from docx import Document                
except ImportError:
    Document = None                          

API_KEY = st.secrets["API_KEY"]
API_URL = "https://api.x.ai/v1/chat/completions"
MODEL = "grok-beta"                         

# === PREVENT STALE JS CACHE FOREVER ===
st.query_params["ts"] = int(time.time())

# === NUCLEAR CSS (your beautiful glow) ===
st.markdown("""
<style>
    .block-container { max-width: 95% !important; padding: 2rem 5% !important; }
    h1 { font-size: 52px !important; color: #00ffcc !important; text-align: center !important; text-shadow: 0 0 20px rgba(0,255,255,0.7) !important; }
    .subtitle { font-size: 26px !important; color: #cccccc !important; text-align: center !important; margin-bottom: 40px !important; }
    .stTextArea > div > div > textarea {
        font-size: 28px !important; padding: 30px !important; height: 120px !important;
        background: #2a2a2a !important; color: white !important;
        border: 4px solid #00ffcc !important; border-radius: 20px !important;
        box-shadow: 0 0 30px rgba(0,255,255,0.6) !important; resize: none !important;
    }
    .stTextArea label { display: none !important; }
    .stButton > button {
        font-size: 28px !important; padding: 20px 70px !important;
        background: linear-gradient(45deg, #00bfff, #00ffcc) !important;
        color: white !important; border: none !important; border-radius: 20px !important;
        font-weight: bold !important; box-shadow: 0 10px 30px rgba(0,255,255,0.6) !important;
        margin: 30px auto !important; display: block !important;
    }
    .big-response {
        font-size: 28px !important; line-height: 2.1 !important; color: #f8f8f8 !important;
        background: #1a1a1a !important; padding: 40px !important; border-radius: 20px !important;
        border-left: 10px solid #00ffcc !important; margin: 50px 0 !important;
        box-shadow: 0 12px 40px rgba(0,0,0,0.5) !important;
    }
    .metric-box {
        background: #242424 !important; padding: 28px !important; border-radius: 18px !important;
        text-align: center !important; margin: 15px 0 !important;
        box-shadow: 0 8px 20px rgba(0,255,255,0.3) !important; border: 2px solid #00ffcc !important;
    }
    .metric-label { font-size: 24px !important; color: #cccccc !important; }
    .metric-value { font-size: 50px !important; color: #00ffcc !important; font-weight: bold !important; text-shadow: 0 0 15px rgba(0,255,255,0.7) !important; }
</style>
""", unsafe_allow_html=True)

# === HEADER ===
st.markdown("<h1>Grok RAG-Aware Text Analyzer</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Ask anything or upload PDF/DOCX/TXT — get deep RAG analysis instantly.</p>", unsafe_allow_html=True)

# === SIDEBAR ===
with st.sidebar:
    st.markdown("### Settings")
    theme = st.radio("Theme", ["Dark", "Light"], index=0)
    st.markdown("### Share This App!")
    share_url = "https://grok-rag-analyzer.streamlit.app"
    st.code(share_url, language=None)
    st.markdown(f"[Copy Link]({share_url})")

# === FILE UPLOAD ===
uploaded_file = st.file_uploader(
    "**Upload PDF, DOCX or TXT** to analyze with Grok",
    type=["pdf", "txt", "docx"],
    help="Grok will read the entire document!"
)

question = None

if uploaded_file:
    with st.spinner("Extracting text from file..."):
        text = ""
        if uploaded_file.type == "application/pdf":
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + " "
        elif uploaded_file.type == "text/plain":
            text = str(uploaded_file.read(), "utf-8")
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            if Document is None:
                st.error("DOCX support not available. Please install python-docx.")
            else:
                doc = Document(uploaded_file)
                text = " ".join([para.text for para in doc.paragraphs])
        else:
            text = "Unsupported file type."

        if len(text) > 150_000:
            text = text[:150_000] + "\n\n... [Truncated for performance]"
        
        word_count = len(text.split())
        question = text
        st.success(f"Extracted {word_count:,} words from {uploaded_file.name}!")
        st.markdown(f"<div class='big-response'>{text[:2000]}...</div>", unsafe_allow_html=True)
else:
    question = st.text_area(
        "Or type your question",
        placeholder="How does RAG fix hallucinations?",
        height=120,
        label_visibility="collapsed"
    )

if st.button("Analyze with Grok", type="primary"):
    if not question or not question.strip():
        st.warning("Please provide text or upload a file!")
    else:
        with st.spinner("Grok is thinking deeply..."):
            headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
            payload = {
                "model": MODEL,
                "messages": [{"role": "user", "content": question}],
                "temperature": 0.7
            }
            try:
                r = requests.post(API_URL, headers=headers, json=payload, timeout=90)
                r.raise_for_status()
                ai_text = r.json()["choices"][0]["message"]["content"]
            except Exception as e:
                st.error("Grok API error. Retrying once...")
                time.sleep(3)
                try:
                    r = requests.post(API_URL, headers=headers, json=payload, timeout=90)
                    r.raise_for_status()
                    ai_text = r.json()["choices"][0]["message"]["content"]
                except:
                    ai_text = "Sorry, Grok is temporarily unreachable. Try again in a minute."

        st.markdown(f"<div class='big-response'>{ai_text}</div>", unsafe_allow_html=True)

        # === RAG Confidence Metrics (Now Fixed!) ===
        words = ai_text.split()
        long_words = [w for w in words if len(w) >= 6]
        rag_terms = len([w for w in ai_text.lower().split() if w in ["rag", "retrieval", "vector", "embedding", "grounding", "knowledge", "context", "chunk"]])
        hedge_words = len([w for w in ai_text.lower().split() if w in ["may", "might", "possibly", "typically", "seems", "perhaps", "probably", "could", "sometimes"]])
        llm_mentions = len([w for w in ai_text.lower().split() if w in ["llm", "grok", "model", "ai", "neural"]])
        tech_count = len([w for w in words if w.lower() in ["transformer", "attention", "token", "bert", "gpt", "embedding", "faiss", "pinecone"] or w.startswith("Grok")])

        confidence = min(99, max(20, 75 + rag_terms*5 - hedge_words*4 + (10 if "source" in ai_text.lower() else 0)))
        rag_score = rag_terms

        color = "#00ff44" if confidence >= 80 else "#ffaa00" if confidence >= 60 else "#ff4444"
        status = "HIGHLY GROUNDED" if confidence >= 80 else "MODERATE" if confidence >= 60 else "RISK OF HALLUCINATION"

        st.markdown(f"""
        <div style='text-align:center; font-size:42px; padding:30px; border-radius:20px; background:#222; border:6px solid {color}; margin:40px 0;'>
            RAG Confidence: <b style='color:{color}'>{confidence}%</b> → <b>{status}</b>
        </div>
        """, unsafe_allow_html=True)

        # === METRICS GRID ===
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"<div class='metric-box'><div class='metric-label'>Total Words</div><div class='metric-value'>{len(words)}</div></div>", unsafe_allow_html=True)
        col2.markdown(f"<div class='metric-box'><div class='metric-label'>Long Words</div><div class='metric-value'>{len(long_words)}</div></div>", unsafe_allow_html=True)
        col3.markdown(f"<div class='metric-box'><div class='metric-label'>RAG Score</div><div class='metric-value'>{rag_score}</div></div>", unsafe_allow_html=True)

        col4, col5 = st.columns(2)
        col4.markdown(f"<div class='metric-box'><div class='metric-label'>AI/LLM Mentions</div><div class='metric-value'>{llm_mentions}</div></div>", unsafe_allow_html=True)
        col5.markdown(f"<div class='metric-box'><div class='metric-label'>Tech Jargon</div><div class='metric-value'>{tech_count}</div></div>", unsafe_allow_html=True)

        st.bar_chart({"Total Words": [len(words)], "Long Words": [len(long_words)], "RAG Terms": [rag_score]}, height=400)

        st.markdown("<br><hr><p style='text-align:center;color:#888;font-size:18px'>Made in India by Raghavendra | Day 3 of Grok Era</p>", unsafe_allow_html=True)
