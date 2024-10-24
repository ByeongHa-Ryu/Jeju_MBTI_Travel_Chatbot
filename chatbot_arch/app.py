import streamlit as st 
from PIL import Image
from callout_form import *

# page config 
st.set_page_config(page_title="🍊MBTI 기반의 제주도 맛집 추천 챗봇! JMT")

## CSS 
st.markdown(
    """
    <style>
    .sidebar-title {
        font-size: 24px;  /* 폰트 크기 조정 */
        font-weight: bold;  /* 글자 굵게 */
        line-height: 1.4;   /* 줄 간격 조정 */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 세션 상태 초기화 
if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferMemory()

if "mbti" not in st.session_state:
    st.session_state.mbti = ""  # MBTI 초기값

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "제주도를 여행하기 딱 좋은 날이네요 😎"}] 


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

    # MBTI 입력값 유지 및 처리
    mbti_input = st.text_input("당신의 MBTI를 대문자로 입력해주세요!", value=st.session_state.mbti)

    if st.button("MBTI 입력"):
        if validate_mbti(mbti_input):
            st.session_state.mbti = mbti_input.upper()  # 입력값 세션 상태에 저장
            st.sidebar.success("혼저옵서예~")
        else:
            st.sidebar.error("유효하지 않은 MBTI 형식입니다.")

    if st.session_state.mbti:
        st.sidebar.markdown(
            f"<h3 style='color:orange;'>당신의 MBTI: {st.session_state.mbti}</h3>",
            unsafe_allow_html=True,
        )
  
    st.divider()  # 구분선 추가 (선택 사항)
    if st.button("대화 초기화"):
        # 대화 초기화 시 기본 메시지로 리셋
        clear_chat_history()
        
# title & subheader 
st.title("안녕하세요!👋")
st.subheader("저는 MBTI 기반의 맛집 추천 챗봇 JMT 에요!")

##이미지 삽입 - git 
#Code here 

# 질문 처리 및 응답 생성
if not st.session_state.mbti:
    st.warning("채팅을 시작하려면 MBTI를 입력해 주세요!")
else:    
    user_input = st.chat_input("저에게 뭐든 물어보세요🍊")

    # 사용자 입력이 있을 때 처리
    if user_input:
        # 사용자 메시지를 세션에 저장
        st.session_state.messages.append({"role": "user", "content": user_input})
        # AI 응답 생성
        with st.chat_message("assistant"):
            with st.spinner("JMT가 생각 중이에요...🤔"):
                try:
                    response = Callout(message=user_input, memory=st.session_state.memory)
                    # AI 응답을 세션에 저장
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.session_state.memory.save_context({"user": user_input}, {"bot": response})

                except Exception as e:
                    error_message = f"에러가 발생했습니다: {e}"
                    st.session_state.messages.append({"role": "assistant", "content": error_message})
        


if st.session_state.messages:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])