# streamlit_app.py
import streamlit as st
import requests
import time

# === CONFIG (SAFE!) ===
API_KEY = st.secrets["API_KEY"]
API_URL = "https://api.x.ai/v1/chat/completions"
MODEL = "grok-3"

# === CSS (INCLUDING BIG DEPLOY BUTTON) ===
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
    .stTextArea > div > div > textarea::placeholder { color: #bbbbbb !important; font-size: 28px !important; }
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

    /* BIG DEPLOY BUTTON */
    .css-1v0mbdj > a {
        font-size: 20px !important; padding: 12px 24px !important;
        background: #00ffcc !important; color: black !important;
        border-radius: 12px !important; font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

# === HEADER ===
st.markdown("<h1>Grok RAG-Aware Text Analyzer</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Ask anything and see deep RAG analysis instantly.</p>", unsafe_allow_html=True)

question = st.text_area("Question", placeholder="How does RAG fix hallucinations?", height=120, key="q")

if st.button("Analyze with Grok"):
    if not question.strip():
        st.warning("Please enter a question!")
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

        st.markdown(f"<div class='big-response'>{ai_text}</div>", unsafe_allow_html=True)

        words = ai_text.split()
        long_words = [w for w in words if len(w) >= 6]
        rag_score = sum(ai_text.lower().count(x) for x in ["rag", "retrieval", "augment", "knowledge"])
        llm_mentions = sum(ai_text.lower().count(x) for x in ["ai", "llm", "model", "token"])
        tech_count = sum(1 for w in words if len(w) > 6 and any(t in w.lower() for t in ["vector", "embed", "prompt", "fine-tune", "hallucination"]))

        col1, col2, col3 = st.columns(3)
        col1.markdown(f"<div class='metric-box'><div class='metric-label'>Total Words</div><div class='metric-value'>{len(words)}</div></div>", unsafe_allow_html=True)
        col2.markdown(f"<div class='metric-box'><div class='metric-label'>Long Words</div><div class='metric-value'>{len(long_words)}</div></div>", unsafe_allow_html=True)
        col3.markdown(f"<div class='metric-box'><div class='metric-label'>RAG Score</div><div class='metric-value'>{rag_score}</div></div>", unsafe_allow_html=True)

        col4, col5 = st.columns(2)
        col4.markdown(f"<div class='metric-box'><div class='metric-label'>AI/LLM Mentions</div><div class='metric-value'>{llm_mentions}</div></div>", unsafe_allow_html=True)
        col5.markdown(f"<div class='metric-box'><div class='metric-label'>Tech Jargon</div><div class='metric-value'>{tech_count}</div></div>", unsafe_allow_html=True)

        st.bar_chart({"Word Count": [len(words)], "Long Words": [len(long_words)], "RAG Score": [rag_score]}, height=450)
