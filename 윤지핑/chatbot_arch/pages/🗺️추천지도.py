import streamlit as st
import pandas as pd
import folium
from folium import plugins
from geopy.distance import geodesic
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
       color: #1E3A8A !important;  /* 진한 파란색 */
   }
   
   /* 선택된 옵션의 텍스트 색상 */
   .stSelectbox > div > div > div {
       color: #87CEFA !important;
   }
   
   /* 드롭다운 메뉴 항목의 텍스트 색상 */
   .stSelectbox > div > div > ul > li {
       color: #87CEFA !important;
   }
   
   /* 멀티셀렉트 선택된 항목 텍스트 */
   .stMultiSelect > div > div > div {
       color: #87CEFA !important;
   }
   
   /* 버튼 스타일링 */
   .stButton>button {
       background-color: #87CEFA !important;  /* 
       color: white !important;
       font-weight: bold;
       border: none;
   }
   
   /* 선택박스 스타일링 */
   .stSelectbox, .stMultiSelect {
       background-color:  white;  /* 앨리스블루 */
       color: white
   }
   
   /* 성공 메시지 스타일링 */
   .stSuccess {
       background-color: #E0FFFF;  /* 연한 청록색 */
   }
   
   /* 정보 메시지 스타일링 */
   .stInfo {
       background-color: #87CEFA;  /* 앨리스블루 */
   }

   /* 지도 페이지 버튼 스타일 */
    [data-testid="stSidebarNav"] a[href="🗺️_제주도_지도"]:not([aria-selected="true"]) {
        background-color: #e3f2fd;  /* 연한 하늘색 배경 */
        border-left: 4px solid #2196F3;
    }
    
    /* 지도 페이지가 선택됐을 때 스타일 */
    [data-testid="stSidebarNav"] a[href="🗺️_제주도_지도"][aria-selected="true"] {
        background-color: #87CEFA;  /* 
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



def get_nearby_places(data, center_lat, center_lng, radius):
    """중심점으로부터 특정 반경 내의 장소들을 필터링하는 함수"""
    if isinstance(data, pd.DataFrame):
        data['distance'] = data.apply(
            lambda row: haversine(
                (center_lat, center_lng), 
                (row['위도'], row['경도']), 
                unit='km'
            ), 
            axis=1
        )
        return data[data['distance'] <= radius].copy()
    else:  # list of spots
        filtered_spots = []
        for spot in data:
            distance = haversine(
                (center_lat, center_lng),
                (float(spot['위도']), float(spot['경도'])),
                unit='km'
            )
            if distance <= radius:
                filtered_spots.append(spot)
        return filtered_spots

def display_accumulated_map():
    st.title("📍 추천 맛집 & 관광지 지도")
    
    # 레이아웃 설정
    col1, col2 = st.columns([7, 3])
    
    # 세션 상태 초기화
    if 'all_restaurants' not in st.session_state:
        st.session_state.all_restaurants = pd.DataFrame()
    if 'all_tourist_spots' not in st.session_state:
        st.session_state.all_tourist_spots = []

    # 세션 상태로 지도 관련 초기값 설정
    if 'map_center' not in st.session_state:
        st.session_state.map_center = [33.384, 126.551]  # 제주도 중심 좌표
    if 'radius' not in st.session_state:
        st.session_state.radius = 50  # 기본 반경 50km
    
    # 사이드바 설정
    with st.sidebar:
        st.header("지도 설정")
        
        # 중심점 선택
        center_options = {
            '제주도 전체': [33.384, 126.551], # 제주도 중심 좌표
            '제주시': [33.499, 126.531],
            '서귀포시': [33.248, 126.563],
            '애월읍': [33.463, 126.306],
            '성산읍': [33.437, 126.917],
            '중문': [33.244, 126.412],
        }
        selected_center = st.selectbox("중심 지역", list(center_options.keys()))
        
        # 반경 설정 (제주도 전체 선택시 비활성화)
        if selected_center == '제주도 전체':
            radius = 50  # 제주도 전체를 커버할 수 있는 반경
            st.info("제주도 전체 지역이 표시됩니다.")
        else:
            radius = st.slider("표시 반경 (km)", 1, 20, 5)
        
        # 표시할 장소 유형
        show_tourist_spots = st.checkbox("관광지 표시", value=True)
        show_restaurants = st.checkbox("음식점 표시", value=True)
    
    # 모든 장소 데이터 준비
    all_places = []
    center = center_options[selected_center]
    
    # 맛집 데이터 처리
    if not st.session_state.all_restaurants.empty and show_restaurants:
        filtered_restaurants = get_nearby_places(
            st.session_state.all_restaurants, 
            center[0], 
            center[1], 
            radius
        )
        
        for _, row in filtered_restaurants.iterrows():
            all_places.append({
                '이름': row['음식점명'],
                '유형': '맛집',
                '위도': float(row['위도']),
                '경도': float(row['경도']),
                '주소': row['주소']
            })
    
    # 관광지 데이터 처리
    if st.session_state.all_tourist_spots and show_tourist_spots:
        # 모든 관광지를 하나의 리스트로 평탄화
        all_tourist_spots = st.session_state.all_tourist_spots
        
        # 필터링 적용
        filtered_spots = get_nearby_places(
            all_tourist_spots,
            center[0],
            center[1],
            radius
        )

        for spot in filtered_spots:
            all_places.append({
                '이름': spot['관광지명'],
                '유형': '관광지',
                '위도': float(spot['위도']),
                '경도': float(spot['경도']),
                '주소': spot['주소']
            })
    
    if all_places:
        # 지도 표시 영역 (왼쪽 컬럼)
        # 기존 col1 (지도) 부분
        with col1:
            # 지도 생성 및 표시 코드는 동일
            center = center_options[selected_center]
            zoom_level = 10 if selected_center == '제주도 전체' else 12
            m = folium.Map(location=center, zoom_start=zoom_level)
            
            if selected_center != '제주도 전체':
                folium.Circle(
                    location=center,
                    radius=radius * 1000,
                    color="gray",
                    fill=True,
                    opacity=0.2
                ).add_to(m)
                
            # 마커 클러스터 및 마커 추가 코드는 동일...
            # 마커 클러스터 생성
            marker_cluster = plugins.MarkerCluster().add_to(m)
            
            # 마커 추가 전 데이터 확인
            if all_places:
                for place in all_places:
                    try:
                        marker_color = 'red' if place['유형'] == '맛집' else 'blue'
                        icon_type = 'cutlery' if place['유형'] == '맛집' else 'info-sign'
                        
                        # 위도, 경도가 유효한지 확인
                        lat = float(place['위도'])
                        lng = float(place['경도'])
                        
                        if not (32 <= lat <= 34) or not (126 <= lng <= 127):
                            continue  # 제주도 영역을 벗어난 좌표는 제외
                        
                        folium.Marker(
                            location=[lat, lng],
                            popup=f"<b>{place['이름']}</b><br>",
                            tooltip=place['이름'],
                            icon=folium.Icon(color=marker_color, icon=icon_type)
                        ).add_to(marker_cluster)
                    except (ValueError, TypeError) as e:
                        continue  # 잘못된 좌표는 건너뛰기
            
            # 지도 표시
            st.components.v1.html(m._repr_html_(), height=600)
            
            st.subheader("📏 거리 계산기")
        
            if len(all_places) < 2:
                st.warning("거리 계산을 위해서는 2개 이상의 장소가 필요합니다.")
            else:
                # 출발지/도착지 선택
                calc_col1, calc_col2 = st.columns(2)
                            
                place_names = [place['이름'] for place in all_places]
                
                with calc_col1:
                    start_place = st.selectbox(
                        "출발지",
                        place_names,
                        key="start_place"
                    )
                
                with calc_col2:
                    end_places = [p for p in place_names if p != start_place]
                    end_place = st.selectbox(
                        "도착지",
                        end_places,
                        key="end_place"
                    )
                
                # 거리 계산 버튼
                if st.button("거리 계산", use_container_width=True):
                    start_data = next(p for p in all_places if p['이름'] == start_place)
                    end_data = next(p for p in all_places if p['이름'] == end_place)
                    
                    distance = haversine(
                        (start_data['위도'], start_data['경도']),
                        (end_data['위도'], end_data['경도']),
                        unit='km'
                    )
                    
                    # 결과를 하나의 컨테이너에 표시
                    results_container = st.container()
                    with results_container:
                        st.success(f"📍 '{start_place}'에서 '{end_place}'까지")
                        st.write(f"🚗 거리: {distance:.1f}km")
                        time_minutes = (distance / 60) * 60
                        st.write(f"⏱️ 예상 소요시간: {int(time_minutes)}분 (평균 속도 60km/h 기준)")

        # 오른쪽 컬럼 (통계 및 목록)
        with col2:
            st.subheader("📊 통계")
            restaurants_count = len([p for p in all_places if p['유형'] == '맛집'])
            tourist_spots_count = len([p for p in all_places if p['유형'] == '관광지'])
            
            if show_restaurants:
                st.write(f"📍 표시된 맛집: {restaurants_count}개")
            if show_tourist_spots:
                st.write(f"🏰 표시된 관광지: {tourist_spots_count}개")
            
            # 장소 목록
            st.subheader("📍 장소 목록")

            df_places = pd.DataFrame(all_places)
            if not df_places.empty:
                st.dataframe(
                    df_places[['이름', '유형']],
                    hide_index=True
                )
    
    else:
        st.info("아직 추천된 장소가 없습니다. 메인 페이지에서 맛집을 추천받아보세요! 🍽️")

if __name__ == "__main__":
    display_accumulated_map()