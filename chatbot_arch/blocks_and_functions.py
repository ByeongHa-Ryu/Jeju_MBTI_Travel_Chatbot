from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.agents.agent_types import AgentType
from langchain_core.output_parsers import StrOutputParser,JsonOutputParser
from langchain.memory import ConversationTokenBufferMemory
from langchain_google_genai import GoogleGenerativeAI # type: ignore
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
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
from mbti_info.mbti import load_mbti_info

def write_log(txt):
    txt_file = open('log.txt','a')
    txt_file.write(txt)
    txt_file.close()

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
    st.session_state.mbti = ""
    st.session_state.messages = [{"role": "assistant", "content": "제주도를 여행하기 딱 좋은 날씨네요 😎"}]
    st.session_state.all_restaurants = []  # 맛집 데이터 초기화
    st.session_state.all_tourist_spots = []  # 관광지 데이터 초기화
    st.session_state.map_center = [33.384, 126.551]  # 지도 중심 좌표 초기화
    st.session_state.radius = 50  # 반경 초기화 (제주도 전체 반경)

#query로 retrieve
def retrieve_mct(loaded_db, query):
   retriever = loaded_db.as_retriever(
       search_type="mmr", 
       search_kwargs={
           "k": 3,
           "fetch_k": 20,
           "lambda_mult": 0.8
       }
   )
   query = f"{query}"
   return retriever.invoke(query)

# 맛집 db load
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

# 관광지 db load
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

#추출된 맛집 데이터의 metadata와 pagecontents 추출
def load_faiss_and_search(query, mbti, month, k=3):
    try:
        loaded_db = load_df(mbti, month)
        retrieve_documents = retrieve_mct(loaded_db, query)
        search_results = []
        for doc in retrieve_documents:
            metadata = doc.metadata
            contents = doc.page_content

            search_results.append({
                'index': metadata['idx'],
                '정보' : contents,
                '위도': float(metadata['위도']) if pd.notna(metadata['위도']) else np.nan,
                '경도': float(metadata['경도']) if pd.notna(metadata['경도']) else np.nan,
            })
  
        return search_results
        
    except Exception as e:
        st.error(f"FAISS 검색 중 오류 발생: {str(e)}")
        return None

# 맛집데이터의 상세정보를 index를 기준으로 csv에서 불러옴
def get_restaurant_details(search_results, restaurants_df):
    try:
        restaurants_data = []
        
        for result in search_results:
            # index기준으로 df에서 정보 가져옴
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
                        
            restaurants_data.append(restaurant_info)

        return restaurants_data

    except Exception as e:
        st.error(f"음식점 정보 조회 중 오류 발생: {str(e)}")
        return None

# 맛집의 위도와 경도를 받아서 관광지데이터와 거리를 모두 계산.
def find_nearby_tourist_spots(restaurant, tourist_spots_df, mbti, month, n=1):
    try:
        # 맛집 한 곳
        restaurant_coords = (restaurant['위도'],restaurant['경도'])
        all_spots = []

        # tourist df랑 추출한 맛집 데이터랑 거리 계산
        for i, tourist in tourist_spots_df.iterrows():
            tourist_coords = (tourist['위도'], tourist['경도'])
            distance = geodesic(restaurant_coords, tourist_coords).kilometers
            
            all_spots.append({
                '관광지명': tourist['관광지명'],
                '주소': tourist['주소'],
                '업종': tourist['소분류'],
                '위도': tourist['위도'],
                '경도': tourist['경도'],
                '거리': distance,
                'idx': i
            })

        # tourst db에서 page content 추출
        tourist_db = load_tour_df(mbti, month)
        all_docs = tourist_db.docstore._dict

        for doc in all_docs.values():
            if doc.metadata.get('idx') == all_spots[0]['idx']:
                all_spots[0]['정보'] = doc.page_content  # matching_docs 정보 추가
                
        # # 거리순으로 정렬해서 세개만
        nearby_spots = sorted(all_spots, key=lambda x: x['거리'])[:n] if all_spots else []
        for doc in all_docs.values():
            if doc.metadata.get('idx') == nearby_spots[0]['idx']:
                 nearby_spots[0]['정보'] = doc.page_content  # matching_docs 정보 추가
        
        
        return nearby_spots
        
    except Exception as e:
        st.error(f"관광지 검색 중 오류 발생: {str(e)}")
        return []

#지도 생성
def create_map_with_restaurants_and_tourists(restaurants_data, tourist_spots):
    try:
        restaurants_df = pd.DataFrame(restaurants_data)
        if restaurants_df is None or restaurants_df.empty:
            st.warning("맛집 데이터가 없습니다.")
            return None
        
        valid_locations = restaurants_df[restaurants_df['위도'].notna() & restaurants_df['경도'].notna()]
            
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
            
            #if idx < len(tourist_spots):
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
            map_key = f"map_{len(st.session_state.messages)}"  # 동적 키 생성
            st_folium(
                map_obj,
                width=700,
                height=500,
                key=map_key,  # 동적 키 사용
                returned_objects=[]
            )
    except Exception as e:
        st.error(f"지도 표시 중 오류 발생: {str(e)}")

@st.cache_data
def create_cached_map(_restaurants_data, _tourist_spots):
    return create_map_with_restaurants_and_tourists(_restaurants_data, _tourist_spots)

def format_restaurant_and_tourist_response(restaurants_data, tourist_spots_data):
    try:
            
        formatted_data = []
        for i in range(len(restaurants_data)):
            restaurant_info = {
                "맛집 설명": restaurants_data[i]['정보'],
                "주변_관광지": [
                    {
                        "관광지 설명": tourist_spots_data[i]['정보'],
                        "거리": f"{tourist_spots_data[i]['거리']:.1f}km"
                    }
                    ]
            }
            formatted_data.append(restaurant_info)
        return formatted_data
        
    except Exception as e:
        return f"정보 포매팅 중 오류 발생: {str(e)}"

def generate_llm_response(query, formatted_data, user_mbti, month):
    try:
        response = llm.invoke(
            input=recommend_inst.format(
            query=query, 
            formatted_data=formatted_data, 
            user_mbti=user_mbti,
            user_mbti_info = load_mbti_info(user_mbti),
            month = month)
        )

        write_log('********************************\n')
        write_log(recommend_inst.format(
            query=query, 
            formatted_data=formatted_data, 
            user_mbti=user_mbti,
            user_mbti_info = load_mbti_info(user_mbti),
            month=month
            ))
        return response
        
    except Exception as e:
        return f"LLM 응답 생성 중 오류 발생: {str(e)}"

# 챗봇 코드 수정
def process_recommendation(message, mbti, month):
    try:
        if 'all_restaurants' not in st.session_state:
            st.session_state.all_restaurants = []
        if 'all_tourist_spots' not in st.session_state:
            st.session_state.all_tourist_spots = []

        restaurants_df = pd.read_csv(f"./chatbot_arch/data/mct_df/{mbti}/mct_{month}_{mbti}.csv")
        tourist_spots_df = pd.read_csv(f"./chatbot_arch/data/tour_df/{mbti}/tour_{month}_{mbti}.csv")

        print("****************************************************************")
        print(f"1. {mbti} {month}월 csv load")        
        print("****************************************************************")

        # 쿼리로 맛집 데이터 세개 검색
        search_results = load_faiss_and_search(message, mbti, month, k=2)
        if not search_results:
            return "죄송합니다. 해당하는 맛집을 찾을 수 없습니다.", None, None
        print(f"2. db에서 search query : {message}")
        print("****************************************************************")
        print("2.5 여기서 쿼리 내용 의도파악 하거니 키워드 추출해서 쿼리를 수정해야할듯 => ex) 쿼리의 의도를 파악해서 쿼리를 수정해줘")
        # 맛집 데이터 정렬
        restaurants_data = get_restaurant_details(search_results, restaurants_df)
        # 관광지 데이터 정렬
        tourist_spots_data = []
        for _, restaurant in pd.DataFrame(restaurants_data).iterrows():
            nearby_spots = find_nearby_tourist_spots(restaurant, tourist_spots_df, mbti, month)
            tourist_spots_data.append(nearby_spots[0])
        # 두 데이터 합쳐서 llm에 입력
        formatted_data = format_restaurant_and_tourist_response(restaurants_data, tourist_spots_data)
        formatted_datas = []
        for i in range(len(restaurants_data)):
            restaurant_info = {
                "맛집": restaurants_data[i]['음식점명'],
                "관광지": tourist_spots_data[i]['관광지명'],
            }
            formatted_datas.append(restaurant_info)
        print("****************************************************************")
        print("3. 맛집 관광지 데이터 포멧팅")
        print("관광지도 가장 가까운거 말고 세개 뽑아서 가장 관련성 있는거 하나를 뽑는게 나을듯")
        print("****************************************************************")
        print(formatted_datas)
              
        # formatted_data에 줄바꿈 문자 추가
        formatted_data = str(formatted_data).replace('}','} \n')
        response = generate_llm_response(message, formatted_data, mbti, month)

        print("****************************************************************")
        print("4. LLM응답")
        print("****************************************************************")
        print(response)

        # 세션 스테이트에 누적 저장
        # 중복제거
        # 맛집 데이터

        if 'all_restaurants' not in st.session_state:
            restaurants_filter = [item for item in restaurants_data if item['음식점명'].replace(' ','') in str(response).replace(' ','')]
            deduplicated_dict = {}
            for item in restaurants_filter:
                restaurant = item['음식점명']
                # 같은 음식점명이 있을 경우 마지막 데이터로 덮어씌워짐
                deduplicated_dict[restaurant] = item
            # 딕셔너리의 값들을 리스트로 변환
            st.session_state.all_restaurants = list(deduplicated_dict.values())
        else:
            # 새로운 데이터 필터링
            restaurants_filter = [item for item in restaurants_data if item['음식점명'].replace(' ','') in str(response).replace(' ','')]
            
            # 기존 데이터를 딕셔너리로 변환
            deduplicated_dict = {rest['음식점명']: rest for rest in st.session_state.all_restaurants}
            
            # 새로운 데이터 추가/업데이트
            for item in restaurants_filter:
                restaurant = item['음식점명']
                deduplicated_dict[restaurant] = item
            
            # 딕셔너리를 다시 리스트로 변환하여 저장
            st.session_state.all_restaurants = list(deduplicated_dict.values())


        if 'all_tourist_spots' not in st.session_state:
            tourist_spots_filter = [item for item in tourist_spots_data if item['관광지명'].replace(' ','') in str(response).replace(' ','')]
            deduplicated_dict = {}
            for item in tourist_spots_filter:
                tourist_spot = item['관광지명']
                # 같은 관광지명이 있을 경우 마지막 데이터로 덮어씌워짐
                deduplicated_dict[tourist_spot] = item
            # 딕셔너리의 값들을 리스트로 변환
            st.session_state.all_tourist_spots = list(deduplicated_dict.values())
        else:
            # 두 데이터를 합치기
            tourist_spots_filter = [item for item in tourist_spots_data if item['관광지명'].replace(' ','') in str(response).replace(' ','')]
            merged_data = st.session_state.all_tourist_spots + tourist_spots_filter
            # 관광지명을 키로 하는 딕셔너리 생성
            # 딕셔너리를 사용하면 자동으로 중복이 제거됨
            deduplicated_dict = {}
            for item in merged_data:
                tourist_spot = item['관광지명']
                # 같은 관광지명이 있을 경우 마지막 데이터로 덮어씌워짐
                deduplicated_dict[tourist_spot] = item

            # 딕셔너리의 값들을 리스트로 변환
            st.session_state.all_tourist_spots = list(deduplicated_dict.values())
            
        print("****************************************************************")
        print('5. 응답기반 session state 수정')
        print("****************************************************************")
        print('[맛집 정보]')

        for restaurant in st.session_state.all_restaurants:
            print(restaurant['음식점명'])   
        print('[관광지]')
        for restaurant in st.session_state.all_tourist_spots:
            print(restaurant['관광지명'])


        return response, restaurants_data, tourist_spots_data
        
    except Exception as e:
        print(f"Error in recommendation process: {e}")
        return f"처리 중 오류가 발생했습니다: {str(e)}", None, None

def state():
    print("[부가질문]")
    print('[맛집 정보]')
    print("********************************")

    for restaurant in st.session_state.all_restaurants:
            print(restaurant['음식점명'])   
            print(restaurant['정보']) 

    print('[관광지 정보]')            
    print("********************************")
    for restaurant in st.session_state.all_tourist_spots:
        print(restaurant['관광지명'])
        print(restaurant['정보']) 

    return st.session_state.all_restaurants, st.session_state.all_tourist_spots