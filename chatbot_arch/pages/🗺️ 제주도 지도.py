import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from haversine import haversine
import streamlit as st
import folium
from folium.plugins import MarkerCluster
from haversine import haversine
import pandas as pd

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

import streamlit as st
import folium
from folium.plugins import MarkerCluster
from haversine import haversine
import pandas as pd
from streamlit_folium import st_folium  # folium_static 대신 st_folium 임포트

@st.cache_data
def load_data():
    """데이터 로드 및 캐싱"""
    tourist_spots = pd.read_csv('관광지위경도.csv')
    restaurants = pd.read_csv('음식점위경도.csv')
    return tourist_spots, restaurants

def get_nearby_places(df, center_lat, center_lng, radius_km=5):
    """중심점 기준 반경 내 장소 필터링"""
    from math import radians, cos, sin, asin, sqrt
    
    def haversine_np(lat1, lng1, lat2, lng2):
        lng1, lat1, lng2, lat2 = map(radians, [lng1, lat1, lng2, lat2])
        dlng = lng2 - lng1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
        return 2 * 6371 * asin(sqrt(a))
    
    distances = df.apply(lambda row: haversine_np(
        center_lat, center_lng, row['위도'], row['경도']
    ), axis=1)
    
    return df[distances <= radius_km]

def main():
    st.title("🗺️ 제주도 맛집 지도")
    
    # 데이터 로드
    tourist_spots, restaurants = load_data()
    
    # 사이드바 설정
    with st.sidebar:
        st.header("지도 설정")
        
        # 중심점 선택
        center_options = {
            '제주시': [33.499, 126.531],
            '서귀포시': [33.248, 126.563],
            '애월읍': [33.463, 126.306],
            '성산읍': [33.437, 126.917],
            '중문': [33.244, 126.412],
        }
        selected_center = st.selectbox("중심 지역", list(center_options.keys()))
        
        # 반경 설정
        radius = st.slider("표시 반경 (km)", 1, 20, 5)
        
        # 표시할 장소 유형
        show_tourist_spots = st.checkbox("관광지 표시", value=True)
        show_restaurants = st.checkbox("음식점 표시", value=True)
        
        if show_restaurants:
            food_types = ['전체'] + list(restaurants['음식종류'].unique())
            selected_food = st.multiselect("음식 종류", food_types, default=['전체'])
    
    # 선택된 중심점 기준으로 데이터 필터링
    center = center_options[selected_center]
    filtered_tourist_spots = get_nearby_places(tourist_spots, center[0], center[1], radius)
    filtered_restaurants = get_nearby_places(restaurants, center[0], center[1], radius)
    
    # 지도 생성
    m = folium.Map(location=center, zoom_start=13)
    marker_cluster = MarkerCluster().add_to(m)
    
    # 마커 추가
    with st.spinner('지도를 불러오는 중...'):
        if show_tourist_spots:
            for _, row in filtered_tourist_spots.iterrows():
                folium.Marker(
                    location=[row['위도'], row['경도']],
                    popup=f"<b>{row['관광지명']}</b>",
                    tooltip=row['관광지명'],
                    icon=folium.Icon(color='blue', icon='info-sign')
                ).add_to(marker_cluster)
        
        if show_restaurants:
            for _, row in filtered_restaurants.iterrows():
                if selected_food == ['전체'] or row['음식종류'] in selected_food:
                    folium.Marker(
                        location=[row['위도'], row['경도']],
                        popup=f"<b>{row['음식점명']}</b><br>{row['음식종류']}",
                        tooltip=row['음식점명'],
                        icon=folium.Icon(color='red', icon='cutlery')
                    ).add_to(marker_cluster)
    
    # 지도 표시
    col1, col2 = st.columns([7, 3])
    with col1:
        loading_placeholder = st.empty()
        loading_placeholder.info('🗺️ 지도를 불러오는 중입니다... 잠시만 기다려주세요.')
        
        try:
            # 지도 로딩
            map_data = st_folium(m, width=1100, height=800)
            # 로딩 메시지 제거
            loading_placeholder.empty()
        except Exception as e:
            loading_placeholder.error('지도 로딩 중 오류가 발생했습니다. 페이지를 새로고침 해주세요.')
            st.error(f"Error: {str(e)}")
    
    with col2:
        st.subheader("📍 통계 정보")
        if show_tourist_spots:
            st.write(f"표시된 관광지 수: {len(filtered_tourist_spots)}")
        if show_restaurants:
            st.write(f"표시된 음식점 수: {len(filtered_restaurants)}")
            if selected_food != ['전체']:
                st.write("선택된 음식 종류:")
                for food in selected_food:
                    st.write(f"- {food}")
        
        # 거리 계산 도구
        st.subheader("📏 거리 계산")
        
        # 현재 표시된 관광지들만 거리 계산에 포함
        visible_locations = {}
        
        # 관광지가 표시되어 있는 경우에만 해당 위치 포함
        if show_tourist_spots:
            for _, row in filtered_tourist_spots.iterrows():
                visible_locations[row['관광지명']] = (row['위도'], row['경도'])
        
        # 음식점이 표시되어 있는 경우에만 해당 위치 포함
        if show_restaurants:
            for _, row in filtered_restaurants.iterrows():
                if selected_food == ['전체'] or row['음식종류'] in selected_food:
                    visible_locations[row['음식점명']] = (row['위도'], row['경도'])
        
        if len(visible_locations) < 2:
            st.warning("거리 계산을 위해서는 2개 이상의 장소가 지도에 표시되어 있어야 합니다.")
        else:
            # 출발지 선택
            start_point = st.selectbox("출발지 선택", list(visible_locations.keys()))
            
            # 도착지 선택 (출발지 제외)
            end_points = [point for point in visible_locations.keys() if point != start_point]
            end_point = st.selectbox("도착지 선택", end_points)
            
            if st.button("거리 계산하기"):
                if start_point and end_point:
                    # 두 지점 간의 거리 계산
                    distance = haversine(
                        visible_locations[start_point], 
                        visible_locations[end_point], 
                        unit='km'
                    )
                    
                    # 결과 표시
                    st.success(f"📍 {start_point}에서 {end_point}까지의 거리:\n\n" + 
                            f"약 {distance:.1f}km")
                    
                    # 예상 이동 시간 계산 (평균 속도 60km/h 가정)
                    time_hours = distance / 60
                    time_minutes = time_hours * 60
                    
                    st.info(f"🚗 예상 이동 시간: 약 {int(time_minutes)}분\n\n" +
                            "(평균 속도 60km/h 기준)")
                    
                    # 경로 정보 추가
                    st.write("🚗 네비게이션 경로 보기:")
                    navi_url = f"https://map.kakao.com/link/to/{end_point}{visible_locations[end_point][0]}{visible_locations[end_point][1]}"
                    st.markdown(f"({navi_url})")

if __name__ == "__main__":
    main()