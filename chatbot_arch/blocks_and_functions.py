from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.agents.agent_types import AgentType
from langchain_core.output_parsers import StrOutputParser,JsonOutputParser
from langchain.memory import ConversationTokenBufferMemory
from langchain_google_genai import GoogleGenerativeAI # type: ignore
from langchain.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.runnables import ConfigurableField

from dotenv import load_dotenv
import os
import pandas as pd
from chatbot_arch.prompts import * 
import streamlit as st
from transformers import AutoTokenizer, AutoModel
import numpy as np 

import folium
from folium import plugins
from streamlit_folium import st_folium
from geopy.distance import geodesic


"""LLM Blocks"""

def mbti_month(mbti, month):
    mbti = mbti
    month = month

load_dotenv()
my_api_key = os.getenv("GOOGLE_API_KEY")

## LLM call 
llm = GoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=my_api_key)

## dataframe agent 
data_dir = './chatbot_arch/data/JEJU_MCT_DATA_final.csv'
df = pd.read_csv(data_dir)

## Data Frame agent on Gemini Engine 
agent = create_pandas_dataframe_agent(
    llm=llm,                           
    df=df,                             
    verbose=True,                      
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION, 
    output_parser=StrOutputParser(),
    prompt=agent_inst,
    allow_dangerous_code=True 
)

def validate_mbti(mbti):
    if len(mbti) != 4:
        return False
    
    valid_pairs = {
        0: {"E", "I"},
        1: {"N", "S"},
        2: {"F", "T"},
        3: {"P", "J"}
    }
    
    return all(mbti[i] in valid_pairs[i] for i in range(4))

def clear_chat_history():
    st.session_state.memory = ConversationTokenBufferMemory(llm=llm, max_token_limit=3000)
    st.session_state.messages = [{"role": "assistant", "content": "제주도를 여행하기 딱 좋은 날씨네요 😎"}]
    st.session_state.all_restaurants = pd.DataFrame()  # 맛집 데이터 초기화
    st.session_state.all_tourist_spots = []  # 관광지 데이터 초기화
    st.session_state.map_center = [33.384, 126.551]  # 지도 중심 좌표 초기화
    st.session_state.radius = 50  # 반경 초기화 (제주도 전체 반경)


def load_df(mbti, month):
    model_name = "upskyy/bge-m3-Korean"
    model_kwargs = {'device': 'cpu'}
    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs
    )

    loaded_db = FAISS.load_local(
        folder_path=f"./chatbot_arch/database/mct_db/{mbti}/{month}",
        index_name=f"mct_{mbti}_{month}",
        embeddings=embeddings,
        allow_dangerous_deserialization=True,
    )

    return loaded_db

def load_tour_df(mbti, month):
    model_name = "upskyy/bge-m3-Korean"
    model_kwargs = {'device': 'cpu'}
    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs
    )

    loaded_tour_db = FAISS.load_local(
        folder_path=f"./chatbot_arch/database/tour_db/{mbti}/{month}",
        index_name=f"tour_{mbti}_{month}",
        embeddings=embeddings,
        allow_dangerous_deserialization=True,
    )

    return loaded_tour_db


def retrieve_mct(loaded_db, query):
   retriever = loaded_db.as_retriever(
       search_type="mmr", 
       search_kwargs={
           "k": 3,
           "fetch_k": 20,
           "lambda_mult": 0.8
       }
   )
   query = f"{query} {st.session_state.get('mbti', '')}"
   return retriever.get_relevant_documents(query)

def load_faiss_and_search(query, mbti, month, k=3,):
    try:
        loaded_db = load_df(mbti, month)
        retrieve_documents = retrieve_mct(loaded_db, query)

        search_results = []
        for doc in retrieve_documents:
            metadata = doc.metadata
            contents = doc.page_content
            try:
                search_results.append({
                    'index': metadata['idx'],
                    '정보' : contents,
                    '위도': float(metadata['위도']) if pd.notna(metadata['위도']) else np.nan,
                    '경도': float(metadata['경도']) if pd.notna(metadata['경도']) else np.nan,
                })
            except (ValueError, TypeError):
                search_results.append({
                    'index': metadata['idx'],
                    '정보' : contents,
                    '위도': np.nan,
                    '경도': np.nan,
                })
        return search_results
        
    except Exception as e:
        st.error(f"FAISS 검색 중 오류 발생: {str(e)}")
        return None

def get_restaurant_details(search_results, restaurants_df, mbti, month):
    try:
        restaurants_data = []
        restaurant_db = load_df(mbti, month)
        all_docs = restaurant_db.docstore._dict

        for result in search_results:
            # Fixed: Added idx key access
            if 'index' in result: # 재방문률
                restaurant = restaurants_df.iloc[result['index']]
                restaurant_info = {
                '음식점명': restaurant['가맹점명'],
                '주소': restaurant['주소'],
                '업종': restaurant['업종'],
                '정보': result['정보'],
                '위도': result['위도'],
                '경도': result['경도'],
                }

            for doc in all_docs.values():
                    if doc.metadata.get('idx') == result['index']:
                        restaurant_info['상세설명'] = doc.page_content
                        break
                        
            restaurants_data.append(restaurant_info)
                
        return pd.DataFrame(restaurants_data)

    except Exception as e:
        st.error(f"음식점 정보 조회 중 오류 발생: {str(e)}")
        return None

def find_nearby_tourist_spots(restaurant_row, tourist_spots_df, mbti, month, n=3):
    try:
        if pd.isna(restaurant_row['위도']) or pd.isna(restaurant_row['경도']):
            return []

        restaurant_coords = (restaurant_row['위도'], restaurant_row['경도'])
        distances = []
        matching_docs = []
        for i, tourist in tourist_spots_df.iterrows():
            if pd.isna(tourist['위도']) or pd.isna(tourist['경도']):
                continue
            try:
                tourist_coords = (tourist['위도'], tourist['경도'])
                distance = geodesic(restaurant_coords, tourist_coords).kilometers
                
                distances.append({
                    '관광지명': tourist['관광지명'],
                    '주소': tourist['주소'],
                    '위도': tourist['위도'],
                    '경도': tourist['경도'],
                    '거리': distance,
                    'idx': i
                })

            except Exception as e:
                print(f"거리 계산 중 오류 발생 (관광지: {tourist['관광지명']}): {str(e)}")
                continue
        
        sorting = sorted(distances, key=lambda x: x['거리'])[:n] if distances else []

        tourist_db = load_tour_df(mbti, month)
        all_docs = tourist_db.docstore._dict
        
        result = []
        for spot in sorting:
            spot_info = spot.copy()  # 기존 거리 정보 복사
            
            # 해당 관광지의 문서 정보 찾기
            for doc in all_docs.values():
                if doc.metadata.get('idx') == spot['idx']:
                    spot_info['상세설명'] = doc.page_content  # matching_docs 정보 추가
                    result.append(spot_info)
                    break
        
        return result
        
    except Exception as e:
        st.error(f"관광지 검색 중 오류 발생: {str(e)}")
        return []

def create_map_with_restaurants_and_tourists(restaurants_df, tourist_spots):
    try:
        if restaurants_df is None or restaurants_df.empty:
            st.warning("맛집 데이터가 없습니다.")
            return None
        
        valid_locations = restaurants_df[restaurants_df['위도'].notna() & restaurants_df['경도'].notna()]
        if valid_locations.empty:
            st.warning("유효한 위치 데이터가 없습니다.")
            return None
            
        center_lat = valid_locations.iloc[0]['위도']
        center_lng = valid_locations.iloc[0]['경도']
        
        m = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=14,
            tiles='CartoDB positron',
            width=800,
            height=600
        )
        
        for idx, row in restaurants_df.iterrows():
            if pd.isna(row['위도']) or pd.isna(row['경도']):
                continue
                
            popup_content = f"""
                <div style='width: 200px'>
                    <h4 style='margin: 0; padding: 5px 0;'>{row['음식점명']}</h4>
                    <p style='margin: 5px 0;'>주소: {row['주소']}</p>
                </div>
            """
            
            folium.Marker(
                location=[row['위도'], row['경도']],
                popup=folium.Popup(popup_content, max_width=300),
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
            
            if idx < len(tourist_spots):
                for tourist in tourist_spots[idx]:
                    if pd.isna(tourist['위도']) or pd.isna(tourist['경도']):
                        continue
                        
                    tourist_popup = f"""
                        <div style='width: 200px'>
                            <h4 style='margin: 0; padding: 5px 0;'>{tourist['관광지명']}</h4>
                            <p style='margin: 5px 0;'>주소: {tourist['주소']}</p>
                        </div>
                    """
                    
                    folium.Marker(
                        location=[tourist['위도'], tourist['경도']],
                        popup=folium.Popup(tourist_popup, max_width=300),
                        icon=folium.Icon(color='blue', icon='info-sign')
                    ).add_to(m)
        
        return m
        
    except Exception as e:
        st.error(f"지도 생성 중 오류 발생: {str(e)}")
        return None

def display_map_with_data(map_obj):
    try:
        if map_obj:
            if 'map_container' not in st.session_state:
                st.session_state.map_container = st.empty()
                
            with st.session_state.map_container:
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
    return create_map_with_restaurants_and_tourists(_restaurants_data, _tourist_spots)

def format_restaurant_and_tourist_response(restaurants_df, tourist_spots):
    try:
        if restaurants_df is None or restaurants_df.empty:
            return "죄송합니다. 맛집을 찾을 수 없습니다."
            
        formatted_data = []
        for idx, row in restaurants_df.iterrows():
            restaurant_info = {
                "맛집 설명": row['상세설명'],
                "주변_관광지": [
                    {
                        "관광지 설명": tourist['상세설명'],
                        "거리": f"{tourist['거리']:.1f}km"
                    }
                    for tourist in tourist_spots[idx]
                ]
            }
            formatted_data.append(restaurant_info)
        print(formatted_data)
        return formatted_data
        
    except Exception as e:
        return f"정보 포매팅 중 오류 발생: {str(e)}"

def generate_llm_response(query, formatted_data, user_mbti=None):
    try:
        response = llm.invoke(
            input=recommend_inst.format(
            query=query, 
            formatted_data=formatted_data, 
            user_mbti=user_mbti)
        )   
        return response
        
    except Exception as e:
        return f"LLM 응답 생성 중 오류 발생: {str(e)}"

# 챗봇 코드 수정
def process_recommendation(message, mbti, month):
    try:
        restaurants_df = pd.read_csv(f"./chatbot_arch/data/mct_df/{mbti}/mct_{month}_{mbti}.csv")
        tourist_spots_df = pd.read_csv(f"./chatbot_arch/data/tour_df/{mbti}/tour_{month}_{mbti}.csv")
        
        search_results = load_faiss_and_search(message, mbti, month, k=3)
        if not search_results:
            return "죄송합니다. 해당하는 맛집을 찾을 수 없습니다.", None, None
            
        restaurants_data = get_restaurant_details(search_results, restaurants_df, mbti, month)
        if restaurants_data is None:
            return "음식점 정보를 가져오는데 실패했습니다.", None, None
            
        tourist_spots = []
        for _, restaurant in restaurants_data.iterrows():
            nearby_spots = find_nearby_tourist_spots(restaurant, tourist_spots_df, mbti, month)
            tourist_spots.append(nearby_spots)  

        formatted_data = format_restaurant_and_tourist_response(restaurants_data, tourist_spots)
        user_mbti = st.session_state.get('mbti', None)
        response = generate_llm_response(message, formatted_data, user_mbti)

        # 세션 스테이트에 누적 저장
        # 중복제거
        if 'all_restaurants' not in st.session_state:
            mask = restaurants_data['음식점명'].apply(lambda x: x in str(response))
            filtered_restaurants = restaurants_data[mask]
            st.session_state.all_restaurants = filtered_restaurants

        else:
            mask = restaurants_data['음식점명'].apply(lambda x: x in str(response))
            filtered_restaurants = restaurants_data[mask]

            # 필터링된 데이터를 기존 데이터와 합치기
            st.session_state.all_restaurants = pd.concat(
                [st.session_state.all_restaurants, filtered_restaurants],
                ignore_index=True
            ).drop_duplicates(subset=['음식점명'])

        tourist_spots_lst = []
        for i in range(3):
            k = tourist_spots[i]
            for j in range(3):
                tourist_spots_lst.append(k[j])
    
        if 'all_tourist_spots' not in st.session_state:
            tourist_spots_filter = [item for item in tourist_spots_lst if item['관광지명'] in str(response)]
            deduplicated_dict = {}
            for item in tourist_spots_filter:
                tourist_spot = item['관광지명']
                # 같은 관광지명이 있을 경우 마지막 데이터로 덮어씌워짐
                deduplicated_dict[tourist_spot] = item
            
            # 딕셔너리의 값들을 리스트로 변환
            st.session_state.all_tourist_spots = list(deduplicated_dict.values())

        else:
            # 두 데이터를 합치기
            merged_data = st.session_state.all_tourist_spots + tourist_spots_lst
            
            # 관광지명을 키로 하는 딕셔너리 생성
            # 딕셔너리를 사용하면 자동으로 중복이 제거됨
            deduplicated_dict = {}
            for item in merged_data:
                tourist_spot = item['관광지명']
                # 같은 관광지명이 있을 경우 마지막 데이터로 덮어씌워짐
                deduplicated_dict[tourist_spot] = item
            
            # 딕셔너리의 값들을 리스트로 변환
            st.session_state.all_tourist_spots = list(deduplicated_dict.values())

        return response, restaurants_data, tourist_spots
        
    except Exception as e:
        print(f"Error in recommendation process: {e}")
        return f"처리 중 오류가 발생했습니다: {str(e)}", None, None