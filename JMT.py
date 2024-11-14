import streamlit as st 
from PIL import Image
from chatbot_arch.callout_form import *
from mbti_info.mbti import *
from langchain.memory import ConversationTokenBufferMemory

# """
# 연한 주황색:
# #FFF5E6 (아주 연한 주황)
# #FFE4B5 (모카신)
# #FFDAB9 (피치 퍼프)

# 중간 주황색:
# #FFA500 (주황)
# #FF8C00 (진한 주황)
# #FF7F50 (산호색)

# 진한 주황색:
# #FF6B35 (붉은 주황)
# #FF4500 (선명한 주황)
# #D35400 (호박색)
# """

# page config 
st.set_page_config(page_title="🍊MBTI 기반의 제주도 맛집 추천 챗봇! JMT", page_icon="🍊")

st.markdown(
    """
    <style>
    /* 폰트 임포트 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Poor+Story&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Jua&display=swap');

    /* 기본 폰트 적용 */
    * {
        font-family: 'Noto Sans KR', sans-serif;
    }

    /* 제목 폰트 - 여러 가능한 클래스명 시도 */
    .st-emotion-cache-10trblm {
        font-family: 'Jua', sans-serif !important;
        font-size: 1.4rem !important;
        color: black !important;
    }

    /* 추가 시도 1 */
    .st-emotion-cache-10trblm e16nr0p30 {
        color: black !important;
    }

    /* 추가 시도 2 */
    h1 {
        color: black !important;
    }

    /* 추가 시도 3 */
    .element-container h1 {
        color: black !important;
    }

    /* 추가 시도 4 */
    [data-testid="stHeader"] {
        color: black !important;
    }
    
    /* 추가 시도 5 */
    div[data-testid="stMarkdownContainer"] h1 {
        color: black !important;
    }

    /* 헤더 내부 제목 스타일링 */
    [data-testid="stHeader"] div {
        font-family: 'Jua', sans-serif !important;
        font-size: 1.8rem !important;
        color: #FF8C00 !important;  /* 주황색으로 설정 */
}

    /* 서브헤더 폰트 */
    .st-emotion-cache-1629p8f {
        font-family: 'Poor Story', cursive;
        color: black !important;
    }

    /* 특정 텍스트 요소에 폰트 적용 */
    h1, h2, h3 {
        font-family: 'Jua', sans-serif !important;
    }

    /* 메인 배경 색상 */
    .stApp {
        background-color: #FFF5E6;
    }
    
    /* 사이드바 스타일링 */
    section[data-testid="stSidebar"] {
        background-color: #FFE4B5;
        border-right: 2px solid #FFA500;
    }
    
    section[data-testid="stSidebar"] > div {
        background-color: #FFE4B5;
        padding: 1rem;
    }
    
    .sidebar-title {
        font-size: 24px;
        font-weight: bold;
        line-height: 1.4;
        color: #000000;
        font-family: 'Jua', sans-serif;
    }
    
    section[data-testid="stSidebar"] .stButton > button {
        background-color: #FF8C00;
        color: black !important;
        border: none;
        font-weight: bold;
        width: 100%;
        font-family: 'Poor Story', cursive;
        font-size: 1.1rem;
    }
    
    section[data-testid="stSidebar"] .stTextInput > div > div > input {
        background-color: white;
        color: black;
        border-color: #FFA500;
    }

    /* 채팅 메시지 스타일링 */
    .stChatMessage {
        background-color: #FFE4B5;
        color: #000000 !important;
        font-family: 'Noto Sans KR', sans-serif;
    }

    
    /* 버튼 스타일링 */
    .stButton>button {
        background-color: #FF8C00;
        color: black !important;
        font-weight: 500;
        font-family: 'Poor Story', cursive;
        font-size: 1.1rem;
    }
    
    /* 입력 필드 스타일링 */
    .stTextInput>div>div>input {
        background-color: white;
        border-color: #FFA500;
        color: #000000;
    }
    
    /* 경고 메시지 스타일링 */
    .stAlert {
        background-color: #FFD700;
        color: #000000;
    }

    /* 일반 텍스트 스타일링 */
    p, .stMarkdown {
        color: #000000 !important;
        font-family: 'Noto Sans KR', sans-serif;
    }

    /* 지도 페이지 네비게이션 스타일 */
    [data-testid="stSidebarNav"] a[href="🗺️_제주도_지도"]:not([aria-selected="true"]) {
        background-color: #e3f2fd;
        border-left: 4px solid #2196F3;
    }
    
    [data-testid="stSidebarNav"] a[href="🗺️_제주도_지도"][aria-selected="true"] {
        background-color: #2196F3;
        color: white;
        border-left: 4px solid #1976D2;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }

    /* 애니메이션 */
    @keyframes slideIn {
        from {
            transform: translateX(-10px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    [data-testid="stSidebarNav"] .st-emotion-cache-1oe5cao {
        animation: slideIn 0.3s ease-out;
        transition: all 0.3s ease;
    }
    
    [data-testid="stSidebarNav"] .st-emotion-cache-1oe5cao:hover {
        transform: scale(1.02);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    /* 상단 헤더 고정 */
    .stApp header {
        position: fixed !important;
        top: 0 !important;
        z-index: 999 !important;
        width: 100% !important;
        background-color: #FFF5E6 !important;
    }
    
    /* 고정 헤더 아래 컨텐츠 여백 */
    .main .block-container {
        padding-top: 5rem !important;
    }
    
    /* 제목 스타일링 */
    .title-container {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        background-color: #FFF5E6 !important;
        z-index: 1000 !important;
        padding: 1rem !important;
        text-align: center !important;
        border-bottom: 2px solid #FFA500 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 제목 추가 (CSS의 title-container 클래스 사용)
st.markdown(
    """
    <div class="title-container">
        <h1 style='font-family: "Black Han Sans", sans-serif; color: #FF8C00; margin: 0;'>
               🍊 JEJU MBTI TRAVEL 🍊
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)

# 세션 상태 초기화 
if "memory" not in st.session_state:
    st.session_state.memory = ConversationTokenBufferMemory(llm=llm, max_token_limit=3000)

if "mbti" not in st.session_state:
    st.session_state.mbti = ""  # MBTI 초기값

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! MBTI를 입력하시면 제주도 맛집을 추천해드릴게요 😊"}] 


# Sidebar
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-title">
            🍊JMT🍊<br>MBTI 제주도 맛집 추천 챗봇
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Jeju MBTI Travel, JMT")

    #월 입력
    months = ["1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"]

    # MBTI 입력 위에 월 선택 추가
    selected_month = st.sidebar.selectbox("여행 시기를 선택하세요", months)
    if 'selected_month' not in st.session_state:
        st.session_state.month = selected_month
    
    # MBTI 입력값 유지 및 처리
    mbti_input = st.text_input("당신의 MBTI를 대문자로 입력해주세요!", value=st.session_state.mbti)

    if st.button("대화 시작"):
        if validate_mbti(mbti_input):
            st.session_state.mbti = mbti_input.upper()  # 입력값 세션 상태에 저장
            st.session_state.messages = [{"role": "assistant", "content": f"안녕하세요! {st.session_state.mbti}유형이시군요! 제주도 맛집에 대해 무엇이든 물어보세요 🍊"}]
            st.sidebar.success("🍊혼저옵서예🍊")
        else:
            st.sidebar.error("유효하지 않은 MBTI 형식입니다.")

    if st.session_state.mbti:
        st.sidebar.markdown(
            f"<h3 style='color:orange;'>당신의 MBTI: {st.session_state.mbti}🪂</h3>",
            unsafe_allow_html=True,
        )
    

    if st.button("대화 초기화"):
        clear_chat_history()
        st.rerun()


if not st.session_state.mbti:
    st.title("🍊JMT와 함께 제주도로 떠나볼까요?👋")
    st.subheader("당신의 MBTI를 입력해주세요!")
    
    # MBTI 입력 전 메시지 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
# 메인 화면 - MBTI 입력 후
else:    
    st.title(f"{st.session_state.month} {st.session_state.mbti} 맞춤형 여행지를 추천해드릴게요👋")
    display_mbti_info(st.session_state.mbti)
    st.subheader("제주도 맛집에 대해 무엇이든 물어보세요!")

    # 기존 메시지들 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
    # 채팅 입력창        
    user_input = st.chat_input("맛집 추천받기 (예: 제주도 흑돼지 맛집 추천해주세요!)🍊")

    # 사용자 입력이 있을 때 처리
    if user_input:
        # 사용자 메시지 표시
        with st.chat_message("user"):
            st.write(user_input)
        
        # 사용자 메시지를 세션에 저장
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # AI 응답 생성
        with st.chat_message("assistant"):
            with st.spinner("JMT가 생각 중이에요...🤔"):
                try:
                    response = Callout(message=user_input, memory=st.session_state.memory, user_mbti = st.session_state.mbti, month = st.session_state.month[0])
                    st.write(response)
                    # AI 응답을 세션에 저장
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.session_state.memory.save_context({"user": user_input}, {"bot": response})

                except Exception as e:
                    error_message = f"에러가 발생했습니다: {e}"
                    st.write(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})