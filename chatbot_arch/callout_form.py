import os
from contextlib import redirect_stdout
import io
from prompts import *
from blocks_and_functions import *
import streamlit as st
import folium
from streamlit_folium import folium_static
import google.generativeai as genai
import json
import re
from langchain.vectorstores import FAISS
from streamlit_folium import st_folium
import random
from langchain_community.embeddings import HuggingFaceEmbeddings


embeddings = HuggingFaceEmbeddings(
    model_name="jhgan/ko-sroberta-multitask",  # 한국어 임베딩 모델
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)
## user_mbti
def Callout(message,memory,user_mbti):
    try:
        # Query classification 
        classification_response = llm.invoke(input=cls_llm_inst.format(input_query=message,memory = memory))

        if "분석 관련" in classification_response:
            print(message, ': cls 임시 print문 : 분석')
            
            # process for sending Verbose of the agent to the post processor 
            f = io.StringIO()
            with redirect_stdout(f):
                analysis_result = agent.invoke(
                    input=message)
                
            verbose_output = f.getvalue()
            #print(verbose_output)
            
            # post processor 
            final_response = llm.invoke(
                input=post_agent_inst.format(
                    input_query = message,
                    verbose_output = verbose_output,
                    analysis_result = analysis_result
                    )
            )
        
        ### 여기 변경
        elif "추천 관련" in classification_response:
            print('cls 임시 print문 : 추천')
            
            try:
                # 세션 상태 초기화
                if 'current_map' not in st.session_state:
                    st.session_state.current_map = None
                    
                # 추천 처리
                final_response, restaurants_data, tourist_spots = process_recommendation(message)
                
                if restaurants_data is not None and tourist_spots is not None:
                    # 컨테이너 생성
                    if 'title_container' not in st.session_state:
                        st.session_state.title_container = st.container()
                    if 'map_section' not in st.session_state:
                        st.session_state.map_section = st.container()
                    if 'info_section' not in st.session_state:
                        st.session_state.info_section = st.container()
                        
                    # 타이틀 표시
                    with st.session_state.title_container:
                        st.subheader("🗺️ 추천 맛집과 주변 관광지")
                    
                    # 지도 섹션
                    with st.session_state.map_section:
                        # 캐시된 지도 생성
                        map_obj = create_cached_map(restaurants_data, tourist_spots)
                        
                        if map_obj:
                            st.session_state.current_map = map_obj
                            # 지도 표시
                            display_map_with_data(map_obj)
                    
                    # 정보 섹션
                    with st.session_state.info_section:
                        with st.expander("📍 상세 정보", expanded=True):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write("추천 맛집")
                                if not restaurants_data.empty:
                                    st.dataframe(
                                        restaurants_data[['음식점명']],
                                        hide_index=True
                                    )
                            
                            with col2:
                                st.write("주변 관광지")
                                tourist_data = []
                                for idx, restaurant in restaurants_data.iterrows():
                                    if idx < len(tourist_spots):
                                        for spot in tourist_spots[idx]:
                                            tourist_data.append({
                                                '관광지명': spot['관광지명'],
                                                '거리': f"{spot['거리']:.1f}km"
                                            })
                                if tourist_data:
                                    st.dataframe(
                                        pd.DataFrame(tourist_data),
                                        hide_index=True
                                    )
                    
                    # 응답 표시
                    st.write(final_response)
                    
            except Exception as e:
                final_response = f"맛집 추천 처리 중 에러가 발생했습니다: {e}"
                print(f"Error in recommendation: {e}")
        

        
        
        else:
            print('cls 임시 print문 : 일반 질문')
            final_response = llm.invoke(
                input=main_persona.format(input_query=message,memory = memory)
            )

    except Exception as e:
        final_response = f"에러가 발생했습니다: {e}"

    return final_response

