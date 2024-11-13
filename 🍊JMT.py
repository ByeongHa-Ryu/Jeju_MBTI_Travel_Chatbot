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
st.set_page_config(page_title="🍊MBTI 기반의 제주도 맛집 추천 챗봇! JMT", layout='wide')

## CSS 
st.markdown(
    """
    <style>
    /* 메인 배경 색상 */
    .stApp {
        background-color: #FFF5E6;
    }
    
    /* 사이드바 스타일링 */
    section[data-testid="stSidebar"] {
        background-color: #FFE4B5;  /* 사이드바 배경색 */
        border-right: 2px solid #FFA500;  /* 사이드바 구분선 */
    }
    
    /* 사이드바 내부 스타일링 */
    section[data-testid="stSidebar"] > div {
        background-color: #FFE4B5;  /* 사이드바 내부 배경색 */
        padding: 1rem;  /* 내부 여백 */
    }
    
    /* 사이드바 제목 스타일 */
    .sidebar-title {
        font-size: 24px;
        font-weight: bold;
        line-height: 1.4;
        color: #000000;
    }
    
    /* 사이드바 버튼 스타일 */
    section[data-testid="stSidebar"] .stButton > button {
        background-color: #FF8C00;
        color: black !important;
        border: none;
        font-weight: bold;
        width: 100%;  /* 버튼 너비 */
    }
    
    /* 사이드바 텍스트 입력 필드 */
    section[data-testid="stSidebar"] .stTextInput > div > div > input {
        background-color: white;
        color: black;
        border-color: #FFA500;
    }

    /* 채팅 메시지 스타일링 */
    .stChatMessage {
        background-color: #FFE4B5;
        color: #000000 !important;
    }
    
    /* 버튼 스타일링 */
    .stButton>button {
        background-color: #FF8C00;
        color: black !important;
        font-weight: bold;
    }
    
    /* 입력 필드 스타일링 */
    .stTextInput>div>div>input {
        background-color: #FF8C00;
        border-color: #FFA500;
        color: #000000; # 테두리
    }
    
    /* 경고 메시지 스타일링 */
    .stAlert {
        background-color: #FFD700;
        color: #000000;
    }

    /* 일반 텍스트 스타일링 */
    p, h1, h2, h3, h4, h5, h6, .stMarkdown {
        color: #000000 !important;
    }

    /* 지도 페이지 버튼 스타일 */
    [data-testid="stSidebarNav"] a[href="🗺️_제주도_지도"]:not([aria-selected="true"]) {
        background-color: #e3f2fd;  /* 연한 하늘색 배경 */
        border-left: 4px solid #2196F3;
    }
    
    /* 지도 페이지가 선택됐을 때 스타일 */
    [data-testid="stSidebarNav"] a[href="🗺️_제주도_지도"][aria-selected="true"] {
        background-color: #2196F3;  /* 진한 하늘색 배경 */
        color: white;
        border-left: 4px solid #1976D2;  /* 더 진한 하늘색 보더 */
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }

   /* 애니메이션 정의 */
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
    
    /* 사이드바 네비게이션 아이템 애니메이션 */
    [data-testid="stSidebarNav"] .st-emotion-cache-1oe5cao {
        animation: slideIn 0.3s ease-out;
        transition: all 0.3s ease;
    }
    
    /* 호버 효과 */
    [data-testid="stSidebarNav"] .st-emotion-cache-1oe5cao:hover {
        transform: scale(1.02);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    </style>
    """,
    unsafe_allow_html=True,
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
            MBTI 기반의<br>🍊제주도 맛집 추천 챗봇! JMT
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Jeju MBTI Travel Guide, JMT")

    #월 입력
    months = ["1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"]

    # MBTI 입력 위에 월 선택 추가
    selected_month = st.sidebar.selectbox("여행 시기를 선택하세요", months)
    if 'selected_month' not in st.session_state:
        st.session_state.month = selected_month
    
    # MBTI 입력값 유지 및 처리
    mbti_input = st.text_input("당신의 MBTI를 대문자로 입력해주세요!", value=st.session_state.mbti)

    if st.button("MBTI 입력"):
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


def extract_restaurant_info(response):
    """
    AI 응답에서 맛집 정보를 추출하여 데이터프레임으로 변환하는 함수
    """
    data = {
        "맛집명": ["온더스톤브런치카페제주성산점", "디뷰"],
        "주소": ["제주 서귀포시 성산읍 오조리 374번지 H동 1층", "제주 제주시 삼양일동 1569-26번지"],
        "대표메뉴": ["카페", "카페"],
        "가격대": ["30,000원", "25,000원"],
        "평점": ["4.5/5", "4.3/5"]
    }
    return pd.DataFrame(data)

if not st.session_state.mbti:
    st.markdown('<div class="title-container">', unsafe_allow_html=True)
    st.title("제주도 맛집 추천 챗봇 JMT입니다! 👋")
    st.subheader("당신의 MBTI를 입력해주세요!")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    st.markdown('</div>', unsafe_allow_html=True)
    
else:    
    st.markdown('<div class="title-container">', unsafe_allow_html=True)
    st.title(f"{st.session_state.month} {st.session_state.mbti} 맞춤형 여행지를 추천해드릴게요! 👋")
    display_mbti_info(st.session_state.mbti)
    st.subheader("제주도 맛집에 대해 무엇이든 물어보세요!")
    st.markdown('</div>', unsafe_allow_html=True)

    # Create two columns
    col1, col2 = st.columns([7, 3])

    # Chat container (left column)
    with col1:
        chat_container = st.container()
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.write(message["content"])
        st.markdown('</div>', unsafe_allow_html=True)

    # Restaurant info (right column)
    with col2:
        st.markdown('<div class="right-column">', unsafe_allow_html=True)
        st.subheader("🍽️ 추천 맛집 정보")
        
        if 'current_restaurants' in st.session_state and st.session_state.current_restaurants is not None:
            # 데이터프레임 스타일링
            st.dataframe(
                st.session_state.current_restaurants,
                hide_index=True,
                use_container_width=True,
                height=400
            )
        else:
            st.info("맛집을 추천받으면 이곳에 정보가 표시됩니다! 🍽️")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Fixed chat input at bottom
    st.markdown('<div class="fixed-chat-input">', unsafe_allow_html=True)
    user_input = st.chat_input("맛집 추천받기 (예: 제주도 흑돼지 맛집 추천해주세요!)🍊")
    st.markdown('</div>', unsafe_allow_html=True)

    if user_input:
        with chat_container:
            with st.chat_message("user"):
                st.write(user_input)
            
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            with st.chat_message("assistant"):
                with st.spinner("JMT가 생각 중이에요...🤔"):
                    try:
                        response = Callout(message=user_input, memory=st.session_state.memory, user_mbti=st.session_state.mbti, month=st.session_state.month[0])
                        st.write(response)
                        
                        restaurant_data = extract_restaurant_info(response)
                        
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        st.session_state.memory.save_context({"user": user_input}, {"bot": response})
                        st.session_state.current_restaurants = restaurant_data

                    except Exception as e:
                        error_message = f"에러가 발생했습니다: {e}"
                        st.write(error_message)
                        st.session_state.messages.append({"role": "assistant", "content": error_message})


