from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.agents.agent_types import AgentType
from langchain_core.output_parsers import StrOutputParser,JsonOutputParser
from langchain.memory import ConversationBufferMemory
from langchain_google_genai import GoogleGenerativeAI # type: ignore
from dotenv import load_dotenv
import os
from prompts import cls_llm_inst
import pandas as pd
from prompts import * 
import streamlit as st
from transformers import AutoTokenizer, AutoModel
import numpy as np 
import folium
from folium import plugins
import streamlit as st
from streamlit_folium import st_folium
from geopy.distance import geodesic
# import FAISS
# import torch

"""LLM Blocks"""

load_dotenv()
my_api_key = os.getenv("GOOGLE_API_KEY")


## LLM call 
llm = GoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=my_api_key)

## dataframe agent 
data_dir = 'data/JEJU_MCT_DATA_v2.csv'
df = pd.read_csv(data_dir,encoding='cp949')


## Data Frame agent on Gemini Engine 
agent = create_pandas_dataframe_agent(
    llm=llm,                           
    df=df,                             
    verbose=True,                      
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION, 
    output_parser = StrOutputParser(),
    prompt = agent_inst,
    allow_dangerous_code=True 
)

# RAG 
# device settings 
# # device = "cuda" if torch.cuda.is_available() else "cpu"
# model_name = "jhgan/ko-sroberta-multitask"
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# embedding_model = AutoModel.from_pretrained(model_name).to(device)

# # embedding func
# def embed_text(text):
#     # 토크나이저의 출력도 GPU로 이동
#     inputs = tokenizer(text, return_tensors='pt', padding=True, truncation=True).to(device)
#     with torch.no_grad():
#         # 모델의 출력을 GPU에서 연산하고, 필요한 부분을 가져옴
#         embeddings = embedding_model(**inputs).last_hidden_state.mean(dim=1)
#     return embeddings.squeeze().cpu().numpy()  # 결과를 CPU로 이동하고 numpy 배열로 변환

# def generate_response_with_faiss(
#     question, df, embeddings, model, embed_text, 
#     time, local_choice, index_path=os.path.join(module_path, 'faiss_index.index'), 
#     max_count=10, k=3, print_prompt=True):
#     return None

import folium
from folium import plugins
import streamlit as st
from streamlit_folium import st_folium
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
import numpy as np

### 여기 변경
### 임베딩, retriever, metadata 등 추가해야함

def load_faiss_and_search(query, k=1):
    """FAISS DB에서 쿼리와 관련된 맛집 검색"""
    try:
        # 임베딩 모델 초기화
        embeddings = HuggingFaceEmbeddings(
            model_name="jhgan/ko-sroberta-multitask",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # FAISS 로드
        db = FAISS.load_local(
            "faiss_db", 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        
        # 검색 쿼리 생성
        search_query = f"{query} {st.session_state.get('mbti', '')}"
        docs_with_scores = db.similarity_search_with_score(search_query, k=k)
        
        # 검색 결과를 데이터프레임으로 변환
        search_results = []
        for doc, score in docs_with_scores:
            metadata = doc.metadata
            
            # 위도, 경도 값이 nan인 경우 처리
            try:
                search_results = [{'idx': 77, '위도': 33.2455473, '경도': 126.5644088}, {'idx': 4, '위도': 33.3700283, '경도': 126.2392054}, {'idx': 106, '위도': 33.3189962, '경도': 126.3456767}]
                # lat = float(metadata['위도']) if pd.notna(metadata['위도']) else np.nan
                # lng = float(metadata['경도']) if pd.notna(metadata['경도']) else np.nan
                
                # search_results.append({
                #     'index': metadata.get('index', None),  # index가 없는 경우 None 반환
                #     '위도': lat,
                #     '경도': lng,
                #     'similarity_score': score
                # })
            except (ValueError, TypeError):
                search_results = [{'idx': 77, '위도': 33.2455473, '경도': 126.5644088}, {'idx': 4, '위도': 33.3700283, '경도': 126.2392054}, {'idx': 106, '위도': 33.3189962, '경도': 126.3456767}]

                # 변환 불가능한 값이 있는 경우
                # search_results.append({
                #     'index': metadata.get('index', None),
                #     '위도': np.nan,
                #     '경도': np.nan,
                #     'similarity_score': score
                # })


        
        return search_results
        
    except Exception as e:
        st.error(f"FAISS 검색 중 오류 발생: {str(e)}")
        return None

def get_restaurant_details(search_results, restaurants_df):
    """검색 결과를 바탕으로 음식점 상세 정보 조회"""
    try:
        restaurants_data = []
        for result in search_results:
            restaurant = restaurants_df.iloc[result['idx']]
            restaurants_data.append({
                '음식점명': restaurant['음식점명'],
                # '주소': restaurant['주소'],
                '위도': result['위도'],
                '경도': result['경도'],
                # 'similarity_score': result['similarity_score']
            })
        print(restaurants_data)
        return pd.DataFrame(restaurants_data)

    except Exception as e:
        st.error(f"음식점 정보 조회 중 오류 발생: {str(e)}")
        return None

def find_nearby_tourist_spots(restaurant_row, tourist_spots_df, n=2):
    """음식점 근처의 관광지 찾기"""
    try:
        # 음식점 좌표가 NaN인 경우 빈 리스트 반환
        if pd.isna(restaurant_row['위도']) or pd.isna(restaurant_row['경도']):
            return []

        # 음식점 좌표
        restaurant_coords = (restaurant_row['위도'], restaurant_row['경도'])
        
        # 각 관광지와의 거리 계산
        distances = []
        for _, tourist in tourist_spots_df.iterrows():
            # 관광지 좌표가 NaN인 경우 건너뛰기
            if pd.isna(tourist['위도']) or pd.isna(tourist['경도']):
                continue
                
            try:
                tourist_coords = (tourist['위도'], tourist['경도'])
                distance = geodesic(restaurant_coords, tourist_coords).kilometers
                
                distances.append({
                    '관광지명': tourist['관광지명'],
                    # '주소': tourist['주소'],
                    '위도': tourist['위도'],
                    '경도': tourist['경도'],
                    '거리': distance
                })
            except Exception as e:
                # 개별 거리 계산 중 오류 발생 시 해당 관광지 건너뛰기
                print(f"거리 계산 중 오류 발생 (관광지: {tourist['관광지명']}): {str(e)}")
                continue
        
        # 거리순으로 정렬하고 상위 n개 선택
        if distances:  # distances가 비어있지 않은 경우에만 정렬
            distances.sort(key=lambda x: x['거리'])
            return distances[:n]
        else:
            return []
        
    except Exception as e:
        st.error(f"관광지 검색 중 오류 발생: {str(e)}")
        return []

def create_map_with_restaurants_and_tourists(restaurants_df, tourist_spots):
    """맛집과 주변 관광지를 표시하는 지도 생성"""
    try:
        if restaurants_df is None or restaurants_df.empty:
            st.warning("맛집 데이터가 없습니다.")
            return None
        
        # NaN이 아닌 첫 번째 위치를 찾아 중심 좌표로 설정
        valid_locations = restaurants_df[restaurants_df['위도'].notna() & restaurants_df['경도'].notna()]
        if valid_locations.empty:
            st.warning("유효한 위치 데이터가 없습니다.")
            return None
            
        center_lat = valid_locations.iloc[0]['위도']
        center_lng = valid_locations.iloc[0]['경도']
        
        # 지도 생성
        m = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=14,
            tiles='CartoDB positron',
            width=800,
            height=600
        )
        
        # 맛집 마커 추가 (빨간색)
        for idx, row in restaurants_df.iterrows():
            # NaN 값 확인
            if pd.isna(row['위도']) or pd.isna(row['경도']):
                continue
                
            popup_content = f"""
                <div style='width: 200px'>
                    <h4 style='margin: 0; padding: 5px 0;'>{row['음식점명']}</h4>
                    <p style='margin: 5px 0;'>주소: </p>
                </div>
            """
            
            folium.Marker(
                location=[row['위도'], row['경도']],
                popup=folium.Popup(popup_content, max_width=300),
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
            
            # 해당 맛집의 주변 관광지 마커 추가 (파란색)
            if idx < len(tourist_spots):
                for tourist in tourist_spots[idx]:
                    # 관광지의 위도, 경도 NaN 확인
                    if pd.isna(tourist['위도']) or pd.isna(tourist['경도']):
                        continue
                        
                    tourist_popup = f"""
                        <div style='width: 200px'>
                            <h4 style='margin: 0; padding: 5px 0;'>{tourist['관광지명']}</h4>
                            <p style='margin: 5px 0;'>주소: </p>
                            <p style='margin: 5px 0;'>거리: {tourist['거리']:.1f}km</p>
                        </div>
                    """
                    
                    folium.Marker(
                        location=[tourist['위도'], tourist['경도']],
                        popup=folium.Popup(tourist_popup, max_width=300),
                        icon=folium.Icon(color='blue', icon='info-sign')
                    ).add_to(m)
        
        return m
        
    except Exception as e:
        print(e)

        st.error(f"지도 생성 중 오류 발생: {str(e)}")
        return None

def display_map_with_data(map_obj):
    """생성된 지도를 안정적으로 표시"""
    try:
        if map_obj:
            # 고정된 컨테이너에 지도 표시
            if 'map_container' not in st.session_state:
                st.session_state.map_container = st.empty()
                
            with st.session_state.map_container:
                # 지도를 고정된 키와 함께 표시
                st_folium(
                    map_obj,
                    width=700,
                    height=500,
                    key="persistent_map",
                    returned_objects=[]
                )
                
    except Exception as e:
        st.error(f"지도 표시 중 오류 발생: {str(e)}")

@st.cache_data
def create_cached_map(_restaurants_data, _tourist_spots):
    """지도 생성을 캐시하여 재렌더링 방지"""
    return create_map_with_restaurants_and_tourists(_restaurants_data, _tourist_spots)

def format_restaurant_and_tourist_response(restaurants_df, tourist_spots):
    """맛집과 관광지 정보를 LLM에 전달하기 위한 포맷팅"""
    try:
        if restaurants_df is None or restaurants_df.empty:
            return "죄송합니다. 맛집을 찾을 수 없습니다."
            
        formatted_data = []
        for idx, row in restaurants_df.iterrows():
            restaurant_info = {
                "이름": row['음식점명'],
                # "주소": row['주소'],
                # "유사도_점수": float(row['similarity_score']),
                "주변_관광지": [
                    {
                        "이름": tourist['관광지명'],
                        # "주소": tourist['주소'],
                        "거리": f"{tourist['거리']:.1f}km"
                    }
                    for tourist in tourist_spots[idx]
                ]
            }
            formatted_data.append(restaurant_info)
            
        return formatted_data
        
    except Exception as e:
        return f"정보 포매팅 중 오류 발생: {str(e)}"

def generate_llm_response(query, formatted_data, user_mbti=None):
    """LLM을 사용하여 맛집과 관광지 추천 응답 생성"""
    try:
        prompt = f"""사용자 질문: {query}

        아래는 검색된 맛집과 주변 관광지 정보입니다:
        {formatted_data}

        {f'사용자의 MBTI는 {user_mbti}입니다.' if user_mbti else ''}

        위 정보를 바탕으로 다음 가이드라인에 따라 자연스러운 맛집과 관광지 추천 답변을 작성해주세요:

        1. 친근하고 자연스러운 톤으로 답변을 작성해주세요.
        2. 각 맛집의 장점과 특징을 설명해주세요.
        3. 각 맛집 근처의 관광지도 자연스럽게 소개해주세요.
        4. 맛집과 관광지의 위치적 특성이나 접근성에 대해 언급해주세요.
        5. 사용자의 MBTI가 있다면, 그에 맞춘 설명을 추가해주세요.
        6. 맛집과 관광지를 함께 즐기는 코스를 제안해주세요.
        7. 즐거운 여행이 되길 바라는 멘트로 마무리해주세요.

        답변에서는 위도/경도 정보나 유사도 점수는 언급하지 말아주세요."""

        response = llm.invoke(input=prompt)
        return response
        
    except Exception as e:
        return f"LLM 응답 생성 중 오류 발생: {str(e)}"

def process_recommendation(message):
    """추천 관련 메시지 처리 함수"""
    try:
        # 데이터프레임 로드
        restaurants_df = pd.read_csv('음식점위경도.csv')
        tourist_spots_df = pd.read_csv('관광지위경도.csv')
        
        # 1. FAISS 검색
        search_results = load_faiss_and_search(message, k=3)
        if not search_results:
            return "죄송합니다. 해당하는 맛집을 찾을 수 없습니다.", None, None
            
        # 2. 음식점 상세 정보 조회
        restaurants_data = get_restaurant_details(search_results, restaurants_df)
        if restaurants_data is None:
            return "음식점 정보를 가져오는데 실패했습니다.", None, None
            
        # 3. 주변 관광지 찾기
        tourist_spots = []
        for _, restaurant in restaurants_data.iterrows():
            nearby_spots = find_nearby_tourist_spots(restaurant, tourist_spots_df)
            tourist_spots.append(nearby_spots)
            
        # 4. 지도 생성
        map_obj = create_map_with_restaurants_and_tourists(restaurants_data, tourist_spots)
        
        # 5. LLM 응답용 데이터 준비
        formatted_data = format_restaurant_and_tourist_response(restaurants_data, tourist_spots)
        
        # 6. LLM 응답 생성
        user_mbti = st.session_state.get('mbti', None)
        response = generate_llm_response(message, formatted_data, user_mbti)
        
        return response, restaurants_data, tourist_spots
        
    except Exception as e:
        print(f"Error in recommendation process: {e}")
        return f"처리 중 오류가 발생했습니다: {str(e)}", None, None

"""Fuctions for JMT app"""

## MBTI validate
def validate_mbti(mbti):
    # input length 
    if len(mbti) != 4:
        return False
    
    # input value
    if mbti[0] not in {"E", "I"}: 
        return False
    if mbti[1] not in {"N", "S"}: 
        return False
    if mbti[2] not in {"F", "T"}:
        return False
    if mbti[3] not in {"P", "J"}: 
        return False

    return True  

def clear_chat_history():
    st.session_state.memory = ConversationBufferMemory()
    st.session_state.messages = [{"role": "assistant", "content": "제주도를 여행하기 딱 좋은 날씨네요 😎"}]
