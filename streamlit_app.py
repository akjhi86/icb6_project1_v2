import streamlit as st
import streamlit.components.v1 as components
import json
import os

# 페이지 설정 (전체 화면 최적화)
st.set_page_config(
    page_title="서울 카페 입지 분석 대시보드",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 스트림릿 상단/하단 UI 숨기기
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stAppViewContainer"] {
        padding: 0;
    }
    .stApp > header {
        display: none !important;
    }
    div.block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
        padding-left: 0rem;
        padding-right: 0rem;
    }
    iframe {
        height: 100vh !important;
        width: 100vw !important;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

def load_and_inject():
    # 1. index.html 읽기
    with open("index.html", "r", encoding="utf-8") as f:
        html_content = f.read()

    # 2. dashboard_data.json 읽기
    if os.path.exists("dashboard_data.json"):
        with open("dashboard_data.json", "r", encoding="utf-8") as f:
            json_data = json.load(f)
    else:
        json_data = {"error": "data not found"}

    # 3. HTML에 데이터 주입
    # <script> 태그 바로 다음에 window.DATA 주입 로직 삽입
    injection_code = f"<script>window.DATA = {json.dumps(json_data, ensure_ascii=False)};</script>"
    
    # <body> 태그 시작 직후에 주입
    final_html = html_content.replace("<body", f"{injection_code}<body")
    
    return final_html

try:
    html = load_and_inject()
    # 전체 화면 iframe 렌더링
    components.html(html, height=2000, scrolling=True)
except Exception as e:
    st.error(f"대시보드를 로드하는 중 오류가 발생했습니다: {e}")
    st.info("preprocess.py를 실행하여 dashboard_data.json 파일이 생성되었는지 확인해주세요.")
