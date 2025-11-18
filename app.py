import streamlit as st
import requests
import time


API_KEY = st.secrets["API_KEY"]
API_URL = "https://api.x.ai/v1/chat/completions"
MODEL = "grok-3"

# === FULL NUCLEAR CSS ===
st.markdown("""
<style>
    .block-container { max-width: 95% !important; padding: 2rem 5% !important; }
    h1 { font-size: 52px !important; color: #00ffcc !important; text-align: center !important; text-shadow: 0 0 20px rgba(0,255,255,0.7) !important; }
    .subtitle { font-size: 26px !important; color: #cccccc !important; text-align: center !important; margin-bottom: 40px !important; }

    /* TEXT AREA */
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

    .confidence-box {
        font-size: 36px !important; text-align: center !important; padding: 20px !important;
        border-radius: 20px !important; margin: 30px 0 !important; font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

# === HEADER ===
st.markdown("<h1>Grok RAG-Aware Text Analyzer</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Ask anything or upload PDF/DOCX/TXT — get deep RAG analysis instantly.</p>", unsafe_allow_html=True)

# === SIDEBAR: THEME + SHARE ===
with st.sidebar:
    st.markdown("### Settings")
    theme = st.radio("Theme", ["Dark", "Light"], index=0)
    if theme == "Light":
        st.markdown("<style>body {background:#f0f2f6; color:black;} .big-response {background:#ffffff; color:black; border-left-color:#0066ff;} .metric-box {background:#ffffff; border-color:#0066ff;}</style>", unsafe_allow_html=True)

    st.markdown("### Share This App!")
    share_url = "https://grok-rag-analyzer-fgwobntdbgfvip2pjtyi9.streamlit.app"
    st.code(share_url, language=None)
    st.markdown(f"[Copy Link]({share_url})")

# === FEATURE 1: PDF / DOCX / TXT UPLOAD ===
st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "**Upload PDF, DOCX or TXT** to analyze with Grok",
    type=["pdf", "txt", "docx"],
    help="Grok will read the entire document!"
)

question = None

if uploaded_file:
    with st.spinner("Extracting text from file..."):
        if uploaded_file.type == "application/pdf":
            from pypdf import PdfReader
            reader = PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + " "
        elif uploaded_file.type == "text/plain":
            text = str(uploaded_file.read(), "utf-8")
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            from docx import Document
            doc = Document(uploaded_file)
            text = " ".join([para.text for para in doc.paragraphs])
        else:
            text = "Unsupported file."

        if len(text) > 100_000:
            text = text[:100_000] + "\n\n... [Truncated for performance]"

        question = text
        st.success(f"Extracted {len(text.split())} words from {uploaded_file.name}!")
        st.markdown(f"<small style='color:#888'>Preview (first 1500 chars):</small>", unsafe_allow_html=True)
        st.markdown(f"<div class='big-response'>{text[:1500]}...</div>", unsafe_allow_html=True)
else:
    question = st.text_area(
        "Or type your question",
        placeholder="How does RAG fix hallucinations?",
        height=120,
        key="q"
    )

if st.button("Analyze with Grok"):
    if not question or not question.strip():
        st.warning("Please provide text or upload a file!")
    else:
        with st.spinner("Grok is thinking..."):
            headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
            data = {"model": MODEL, "messages": [{"role": "user", "content": question}], "temperature": 0.7}

            try:
                r = requests.post(API_URL, headers=headers, json=data, timeout=60)
                ai_text = r.json()["choices"][0]["message"]["content"] if r.status_code == 200 else r.text
            except:
                time.sleep(2)
                try:
                    r = requests.post(API_URL, headers=headers, json=data, timeout=60)
                    ai_text = r.json()["choices"][0]["message"]["content"] if r.status_code == 200 else "Failed."
                except:
                    ai_text = "Grok unreachable."

        # === RESPONSE ===
        st.markdown(f"<div class='big-response'>{ai_text}</div>", unsafe_allow_html=True)

        # === ANALYSIS + FEATURE 2: RAG CONFIDENCE + HALLUCINATION DETECTOR ===
        words = ai_text.split()
        long_words = [w for w in words if len(w) >= 6]
        rag_terms = len([w for w in ai_text.lower().split() if w in ["rag", "retrieval", "knowledge", "vector", "embed", "augment"]])
        hedge_words = len([w for w in ai_text.lower().split() if w in ["may", "might", "possibly", "typically", "seems", "perhaps", "probably"]])
        confidence = max(10, min(100, 80 + rag_terms*4 - hedge_words*3))
        is_grounded = rag_terms > 3 and hedge_words < 5

        color = "#00ff44" if confidence >= 80 else "#ffaa00" if confidence >= 60 else "#ff4444"
        status = "HIGHLY GROUNDED" if confidence >= 80 else "MODERATE" if confidence >= 60 else "RISK OF HALLUCINATION"

        st.markdown(f"""
        <div style='text-align:center; font-size:38px; padding:25px; border-radius:20px; background:#222; border:5px solid {color};'>
            RAG Confidence: <b style='color:{color}'>{confidence}%</b> → <b>{status}</b>
        </div>
        """, unsafe_allow_html=True)

        # === METRICS ===
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"<div class='metric-box'><div class='metric-label'>Total Words</div><div class='metric-value'>{len(words)}</div></div>", unsafe_allow_html=True)
        col2.markdown(f"<div class='metric-box'><div class='metric-label'>Long Words</div><div class='metric-value'>{len(long_words)}</div></div>", unsafe_allow_html=True)
        col3.markdown(f"<div class='metric-box'><div class='metric-label'>RAG Score</div><div class='metric-value'>{rag_score}</div></div>", unsafe_allow_html=True)

        col4, col5 = st.columns(2)
        col4.markdown(f"<div class='metric-box'><div class='metric-label'>AI/LLM Mentions</div><div class='metric-value'>{llm_mentions}</div></div>", unsafe_allow_html=True)
        col5.markdown(f"<div class='metric-box'><div class='metric-label'>Tech Jargon</div><div class='metric-value'>{tech_count}</div></div>", unsafe_allow_html=True)

        st.bar_chart({"Words": [len(words)], "Long": [len(long_words)], "RAG": [rag_score]}, height=450)

        st.markdown("<br><hr><p style='text-align:center;color:#888;font-size:18px'>Made with ❤️ by Raghu | Day 2 of 100 Days of GenAI</p>", unsafe_allow_html=True)
