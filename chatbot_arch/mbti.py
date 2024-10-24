import json
import streamlit as st

def load_mbti_info(mbti_type):
    """MBTI 정보를 JSON 파일에서 읽어오는 함수"""
    try:
        with open('mbti_info.json', 'r', encoding='utf-8') as file:
            mbti_data = json.load(file)
            return mbti_data.get(mbti_type, {
                "nickname": "제주 탐험가",
                "travel_style": "제주도의 새로운 매력을 발견하는 여행",
                "food_style": "제주도의 다양한 맛집 탐방"
            })
    except Exception as e:
        print(f"JSON 파일 읽기 오류: {e}")
        # 기본값 반환
        return {
            "nickname": "제주 탐험가",
            "travel_style": "제주도의 새로운 매력을 발견하는 여행",
            "food_style": "제주도의 다양한 맛집 탐방"
        }

def display_mbti_info(mbti_type):
    """MBTI 정보를 안전하게 표시하는 함수"""
    if not mbti_type:
        return
    
    # MBTI 정보 로드
    mbti_info = load_mbti_info(mbti_type.upper())
    
    try:
        st.markdown(f"""
            <div style='
                background-color: #FFE4B5;
                padding: 15px;
                border-radius: 10px;
                border: 2px solid #FFA500;
                margin-bottom: 20px;
            '>
                <div style='display: flex; justify-content: space-between;'>
                    <div style='flex: 1;'>
                        <h3 style='color: #FF6B35; margin: 0;'>{mbti_type} - {mbti_info.get('nickname', '제주 탐험가')}</h3>
                    </div>
                </div>
                <p style='margin: 10px 0 5px 0;'>
                    <strong>🧳 여행 스타일:</strong> {mbti_info.get('travel_style', '제주도의 새로운 매력을 발견하는 여행')}
                </p>
                <p style='margin: 5px 0;'>
                    <strong>🍽️ 음식 스타일:</strong> {mbti_info.get('food_style', '제주도의 다양한 맛집 탐방')}
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )
    except Exception as e:
        print(f"MBTI 정보 표시 오류: {e}")
        # 오류 발생 시 기본 정보 표시
        st.markdown(f"""
            <div style='
                background-color: #FFE4B5;
                padding: 15px;
                border-radius: 10px;
                border: 2px solid #FFA500;
                margin-bottom: 20px;
            '>
                <h3 style='color: #FF6B35; margin: 0;'>{mbti_type} 여행자</h3>
                <p style='margin: 10px 0;'>맛있는 제주도 여행을 함께 즐겨보아요! 🌴</p>
            </div>
            """,
            unsafe_allow_html=True
        )