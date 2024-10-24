import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
from haversine import haversine

# 페이지 설정
st.set_page_config(page_title="🗺️ 제주도 지도", layout="wide")

# CSS 스타일 적용 (메인 페이지와 동일한 스타일)
# CSS 스타일 적용
st.markdown(
   """
   <style>
   /* 메인 배경 색상 */
   .stApp {
       background-color: #E6F3FF;  /* 연한 하늘색 */
   }
   
   /* 사이드바 스타일링 */
   [data-testid="stSidebar"] {
       background-color: #ADD8E6;  /* 연한 파란색 */
   }
   
   [data-testid="stSidebar"] > div {
       background-color: #ADD8E6;
       padding: 1rem;
   }
   
   /* 모든 텍스트 요소에 대한 기본 색상 설정 */
   p, h1, h2, h3, h4, h5, h6, .stMarkdown, span, li, label, .stSelectbox, 
   .stMultiSelect, [data-testid="stMarkdownContainer"] p {
       color: #1E4B6B !important;  /* 진한 파란색 */
   }
   
   /* 선택된 옵션의 텍스트 색상 */
   .stSelectbox > div > div > div {
       color: #1E4B6B !important;
   }
   
   /* 드롭다운 메뉴 항목의 텍스트 색상 */
   .stSelectbox > div > div > ul > li {
       color: #1E4B6B !important;
   }
   
   /* 멀티셀렉트 선택된 항목 텍스트 */
   .stMultiSelect > div > div > div {
       color: #1E4B6B !important;
   }
   
   /* 버튼 스타일링 */
   .stButton>button {
       background-color: #4682B4 !important;  /* 스틸블루 */
       color: white !important;
       font-weight: bold;
       border: none;
   }
   
   /* 선택박스 스타일링 */
   .stSelectbox, .stMultiSelect {
       background-color: #F0F8FF;  /* 앨리스블루 */
   }
   
   /* 성공 메시지 스타일링 */
   .stSuccess {
       background-color: #E0FFFF;  /* 연한 청록색 */
   }
   
   /* 정보 메시지 스타일링 */
   .stInfo {
       background-color: #F0F8FF;  /* 앨리스블루 */
   }
   </style>
   """,
   unsafe_allow_html=True,
)

# 주요 장소 좌표 정의
locations = {
    '제주국제공항': (33.507, 126.493),
    '한라산': (33.362, 126.529),
    '성산일출봉': (33.458, 126.942),
    '중문관광단지': (33.244, 126.412),
    '서귀포시청': (33.2482, 126.5628),
    '제주시청': (33.4996, 126.5312),
    '우도': (33.5219, 126.9514),
    '차귀도': (33.3144, 126.1632),
    '마라도': (33.1144, 126.2686),
    '협재해수욕장': (33.3940, 126.2392)
}

def main():
    st.title("🗺️ 제주도 맛집 지도")
    
    # 제주도 중심 좌표
    jeju_center = [33.399, 126.562]
    
    # 사이드바 설정
    with st.sidebar:
        st.header("지도 설정")
        
        # 지도 스타일 선택
        map_styles = {
            '기본': 'OpenStreetMap',
            '위성': 'Stamen Terrain',
            '밝은': 'CartoDB positron'
        }
        selected_style = st.selectbox("지도 스타일", list(map_styles.keys()))
        
        # 지역 선택
        regions = ['전체', '제주시', '서귀포시', '애월읍', '중문']
        selected_region = st.selectbox("지역 선택", regions)
        
        # 음식 종류 선택
        food_types = ['전체', '흑돼지', '해산물', '카페', '한식', '분식']
        selected_food = st.multiselect("음식 종류", food_types, default=['전체'])

    # 예시 맛집 데이터
    restaurants = {
        '흑돼지 맛집': [33.499, 126.531, '흑돼지'],
        '해물탕 맛집': [33.243, 126.559, '해산물'],
        '카페 맛집': [33.355, 126.699, '카페'],
        '고기국수 맛집': [33.488, 126.500, '한식'],
    }
    
    # 지도 생성
    m = folium.Map(
        location=jeju_center,
        zoom_start=11,
        tiles=map_styles[selected_style]
    )
    
    # 맛집 마커 추가
    for name, info in restaurants.items():
        if (selected_food == ['전체'] or info[2] in selected_food):
            folium.Marker(
                location=[info[0], info[1]],
                popup=f"<b>{name}</b><br>{info[2]}",
                tooltip=name,
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
    
    # 지도와 정보를 나란히 표시
    col1, col2 = st.columns([7, 3])
    
    with col1:
        # 지도 표시
        folium_static(m, width=800, height=600)
        
    with col2:
        # 선택된 정보 표시
        st.subheader("📍 맛집 정보")
        st.write(f"선택된 지역: {selected_region}")
        st.write("선택된 음식 종류:")
        for food in selected_food:
            st.write(f"- {food}")
            
        # 거리 계산 도구
        st.subheader("📏 거리 계산")
        
        # 출발지 선택
        start_point = st.selectbox("출발지 선택", list(locations.keys()))
        
        # 도착지 선택
        end_point = st.selectbox("도착지 선택", list(locations.keys()))
        
        if st.button("거리 계산하기"):
            if start_point and end_point:
                # 두 지점 간의 거리 계산
                distance = haversine(locations[start_point], locations[end_point], unit='km')
                
                # 결과 표시
                st.success(f"📍 {start_point}에서 {end_point}까지의 거리:\n\n" + 
                          f"약 {distance:.1f}km")
                
                # 예상 이동 시간 계산 (평균 속도 60km/h 가정)
                time_hours = distance / 60
                time_minutes = time_hours * 60
                
                st.info(f"🚗 예상 이동 시간: 약 {int(time_minutes)}분\n\n" +
                        "(평균 속도 60km/h 기준)")

if __name__ == "__main__":
    main()