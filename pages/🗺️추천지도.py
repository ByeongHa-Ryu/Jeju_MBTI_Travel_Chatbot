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
    if 'selected_place' not in st.session_state:
        st.session_state.selected_place = None

    # 지도 중심점 설정
    if 'map_center' not in st.session_state:
        st.session_state.map_center = [33.384, 126.551]
    if 'radius' not in st.session_state:
        st.session_state.radius = 50
    
    # 사이드바 설정 (기존 코드와 동일)
    with st.sidebar:
        st.header("지도 설정")
        center_options = {
            '제주도 전체': [33.384, 126.551],
            '제주시': [33.499, 126.531],
            '서귀포시': [33.248, 126.563],
            '애월읍': [33.463, 126.306],
            '성산읍': [33.437, 126.917],
            '중문': [33.244, 126.412],
        }
        selected_center = st.selectbox("중심 지역", list(center_options.keys()))
        
        if selected_center == '제주도 전체':
            radius = 50
            st.info("제주도 전체 지역이 표시됩니다.")
        else:
            radius = st.slider("표시 반경 (km)", 1, 20, 5)
        
        show_tourist_spots = st.checkbox("관광지 표시", value=True)
        show_restaurants = st.checkbox("음식점 표시", value=True)
    
    # 모든 장소 데이터 준비
    all_places = []
    center = center_options[selected_center]
    
    # 맛집과 관광지 데이터 처리 (기존 코드와 동일)
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
                '주소': row['주소'],
                '업종': row['업종']
            })
    
    if st.session_state.all_tourist_spots and show_tourist_spots:
        all_tourist_spots = st.session_state.all_tourist_spots
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
                '주소': spot['주소'],
                '업종': spot['업종']
            })
    
    if all_places:
        # 지도 생성 부분 수정
        with col1:
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
            
            # 선택된 장소가 있으면 해당 위치로 지도 중심 이동
            if st.session_state.selected_place:
                selected_place_data = next(
                    (p for p in all_places if p['이름'] == st.session_state.selected_place),
                    None
                )
                if selected_place_data:
                    m = folium.Map(
                        location=[selected_place_data['위도'], selected_place_data['경도']],
                        zoom_start=15  # 더 가깝게 확대
                    )
            
            # 마커 클러스터 생성
            marker_cluster = plugins.MarkerCluster().add_to(m)
            
            # 마커 추가
            for place in all_places:
                try:
                    lat = float(place['위도'])
                    lng = float(place['경도'])
                    
                    if not (32 <= lat <= 34) or not (126 <= lng <= 127):
                        continue
                    
                    # 선택된 장소인 경우 클러스터 없이 직접 지도에 추가
                    if st.session_state.selected_place and st.session_state.selected_place == place['이름']:
                        folium.Marker(
                            location=[lat, lng],
                            tooltip=f"🌟 <b>{place['이름']}</b><br>{place['주소']}",
                            icon=folium.Icon(color='yellow', icon='star', prefix='fa', size=(150, 150))
                        ).add_to(m)  # 클러스터가 아닌 지도에 직접 추가
                    else:
                        marker_color = 'red' if place['유형'] == '맛집' else 'blue'
                        icon_type = 'cutlery' if place['유형'] == '맛집' else 'info-sign'
                        folium.Marker(
                            location=[lat, lng],
                            popup=f"<b>{place['이름']}</b><br>",
                            tooltip=place['이름'],
                            icon=folium.Icon(color=marker_color, icon=icon_type)
                        ).add_to(marker_cluster)
                except (ValueError, TypeError):
                    continue
        # with col1:
        #     # 지도 생성
        #     center = center_options[selected_center]
        #     zoom_level = 10 if selected_center == '제주도 전체' else 12
        #     m = folium.Map(location=center, zoom_start=zoom_level)
            
        #     if selected_center != '제주도 전체':
        #         folium.Circle(
        #             location=center,
        #             radius=radius * 1000,
        #             color="gray",
        #             fill=True,
        #             opacity=0.2
        #         ).add_to(m)
            
        #     # 마커 클러스터 생성
        #     marker_cluster = plugins.MarkerCluster().add_to(m)
            
        #     # 마커 추가
        #     for place in all_places:
        #         try:
        #             marker_color = 'red' if place['유형'] == '맛집' else 'blue'
        #             icon_type = 'cutlery' if place['유형'] == '맛집' else 'info-sign'
                    
        #             lat = float(place['위도'])
        #             lng = float(place['경도'])
                    
        #             if not (32 <= lat <= 34) or not (126 <= lng <= 127):
        #                 continue
                    
        #             # 선택된 장소인 경우 특별한 마커 스타일 적용
        #             if st.session_state.selected_place and st.session_state.selected_place == place['이름']:
        #                 # 선택된 장소는 큰 노란색 마커로 표시
        #                 folium.Marker(
        #                     location=[lat, lng],
        #                     popup=f"<b>{place['이름']}</b><br>{place['주소']}<br>{place['업종']}",
        #                     tooltip=f"🌟 {place['이름']}",
        #                     icon=folium.Icon(color='yellow', icon='star', prefix='fa')
        #                 ).add_to(m)
        #                 # 선택된 장소로 지도 중심 이동
        #                 m.location = [lat, lng]
        #                 m.zoom_start = 14
        #             else:
        #                 # 일반 마커
        #                 folium.Marker(
        #                     location=[lat, lng],
        #                     popup=f"<b>{place['이름']}</b><br>",
        #                     tooltip=place['이름'],
        #                     icon=folium.Icon(color=marker_color, icon=icon_type)
        #                 ).add_to(marker_cluster)
        #         except (ValueError, TypeError):
        #             continue
            
            # 지도 표시
            st.components.v1.html(m._repr_html_(), height=600)
            
            # 거리 계산기 (기존 코드와 동일)
            # st.subheader("📏 거리 계산기")
            # if len(all_places) < 2:
            #     st.warning("거리 계산을 위해서는 2개 이상의 장소가 필요합니다.")
            # else:
            #     calc_col1, calc_col2 = st.columns(2)
            #     place_names = [place['이름'] for place in all_places]
                
            #     with calc_col1:
            #         start_place = st.selectbox("출발지", place_names, key="start_place")
            #     with calc_col2:
            #         end_places = [p for p in place_names if p != start_place]
            #         end_place = st.selectbox("도착지", end_places, key="end_place")
                
            #     if st.button("거리 계산", use_container_width=True):
            #         start_data = next(p for p in all_places if p['이름'] == start_place)
            #         end_data = next(p for p in all_places if p['이름'] == end_place)
                    
            #         distance = haversine(
            #             (start_data['위도'], start_data['경도']),
            #             (end_data['위도'], end_data['경도']),
            #             unit='km'
            #         )
                    
            #         results_container = st.container()
            #         with results_container:
            #             st.success(f"📍 '{start_place}'에서 '{end_place}'까지")
            #             st.write(f"🚗 거리: {distance:.1f}km")
            #             time_minutes = (distance / 60) * 60
            #             st.write(f"⏱️ 예상 소요시간: {int(time_minutes)}분 (평균 속도 60km/h 기준)")
            # 거리 계산기 부분 수정
            st.subheader("📏 거리 계산기")
            if len(all_places) < 2:
                st.warning("거리 계산을 위해서는 2개 이상의 장소가 필요합니다.")
            else:
                calc_col1, calc_col2 = st.columns(2)
                place_names = [place['이름'] for place in all_places]
                
                with calc_col1:
                    start_place = st.selectbox("출발지", place_names, key="start_place")
                with calc_col2:
                    end_places = [p for p in place_names if p != start_place]
                    end_place = st.selectbox("도착지", end_places, key="end_place")
                
                if st.button("거리 계산", use_container_width=True):
                    start_data = next(p for p in all_places if p['이름'] == start_place)
                    end_data = next(p for p in all_places if p['이름'] == end_place)
                    
                    # 두 지점 사이의 거리 계산
                    distance = haversine(
                        (start_data['위도'], start_data['경도']),
                        (end_data['위도'], end_data['경도']),
                        unit='km'
                    )
                    
                    # 지도 중심점과 줌 레벨 조정
                    center_lat = (float(start_data['위도']) + float(end_data['위도'])) / 2
                    center_lng = (float(start_data['경도']) + float(end_data['경도'])) / 2
                    
                    # 새로운 지도 생성
                    line_map = folium.Map(location=[center_lat, center_lng], zoom_start=12)
                    
                    # 출발지 마커 추가 (초록색)
                    folium.Marker(
                        location=[float(start_data['위도']), float(start_data['경도'])],
                        popup=f"<b>출발: {start_place}</b>",
                        tooltip=f"출발: {start_place}",
                        icon=folium.Icon(color='green', icon='info-sign')
                    ).add_to(line_map)
                    
                    # 도착지 마커 추가 (빨간색)
                    folium.Marker(
                        location=[float(end_data['위도']), float(end_data['경도'])],
                        popup=f"<b>도착: {end_place}</b>",
                        tooltip=f"도착: {end_place}",
                        icon=folium.Icon(color='red', icon='info-sign')
                    ).add_to(line_map)
                    
                    # 두 지점을 잇는 직선 추가
                    points = [
                        [float(start_data['위도']), float(start_data['경도'])],
                        [float(end_data['위도']), float(end_data['경도'])]
                    ]
                    folium.PolyLine(
                        points,
                        weight=3,
                        color='blue',
                        opacity=0.8,
                        dash_array='10'  # 점선으로 표시
                    ).add_to(line_map)
                    
                    # 결과 표시
                    results_container = st.container()
                    with results_container:
                        # 지도 표시
                        st.components.v1.html(line_map._repr_html_(), height=400)
                        
                        # 거리 정보 표시
                        st.success(f"📍 '{start_place}'에서 '{end_place}'까지")
                        st.write(f"🚗 직선 거리: {distance:.1f}km")
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
            
            # 장소 목록과 선택 기능
            st.subheader("📍 장소 목록")
            df_places = pd.DataFrame(all_places)
            
            if not df_places.empty:
                # 선택 가능한 데이터프레임으로 표시
                selected_indices = st.dataframe(
                    df_places[['유형', '이름', '업종', '주소']],
                    hide_index=True,
                    use_container_width=True
                )
                
                # 장소 선택 드롭다운 추가
                selected_place = st.selectbox(
                    "장소 선택",
                    ["선택하세요..."] + list(df_places['이름']),
                    index=0
                )
                
                # 선택된 장소 처리
                if selected_place != "선택하세요...":
                    st.session_state.selected_place = selected_place
                    selected_info = df_places[df_places['이름'] == selected_place].iloc[0]
                    st.info(f"""
                    🏷️ {selected_info['이름']}
                    📍 {selected_info['주소']}
                    🏢 {selected_info['업종']}
                    """)
                else:
                    st.session_state.selected_place = None
    
    else:
        st.info("아직 추천된 장소가 없습니다. 메인 페이지에서 맛집을 추천받아보세요! 🍽️")

if __name__ == "__main__":
    display_accumulated_map()