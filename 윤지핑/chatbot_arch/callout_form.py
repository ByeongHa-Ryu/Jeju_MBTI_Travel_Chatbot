import os
from contextlib import redirect_stdout
import io
from prompts import *
# from blocks_and_functions import *
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
import os
from contextlib import redirect_stdout
import io
from prompts import *
from blocks_and_functions2 import *



## user_mbti
def Callout(message, memory, user_mbti, month):
    try:
        # Query classification 
        classification_response = llm.invoke(input=cls_llm_inst.format(input_query=message,memory = memory,few_shot_prompt_for_cls=few_shot_prompt_for_cls))

        if "분석 관련" in classification_response:
            
            f = io.StringIO()
            with redirect_stdout(f):
                analysis_result = agent.invoke(
                    input=agent_inst.format(
                        input_query = message,
                        data_info_prompt = data_info_prompt
                    ))
                
            verbose_output = f.getvalue()

            final_response = llm.invoke(
                input=post_agent_inst.format(
                    input_query = message,
                    verbose_output = verbose_output,
                    analysis_result = analysis_result
                    )
            )
        
        ### 여기 변경

        elif "추천 관련" in classification_response:
            try:
                # Process recommendation
                final_response, restaurants_data, tourist_spots = process_recommendation(message, user_mbti, month)
                
                if restaurants_data is not None and tourist_spots is not None:
                    # Create containers if they don't exist
                    if 'title_container' not in st.session_state:
                        st.session_state.title_container = st.container()
                    if 'info_section' not in st.session_state:
                        st.session_state.info_section = st.container()
                    
                    # Display title
                    with st.session_state.title_container:
                        st.subheader("🗺️ 추천 맛집과 주변 관광지")
                    
                    # Display detailed information
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

                return final_response
                
            except Exception as e:
                return f"맛집 추천 처리 중 에러가 발생했습니다: {e}"
        
        else:
            final_response = llm.invoke(
                input=main_persona.format(input_query=message,memory = memory)
            )

    except Exception as e:
        final_response = f"에러가 발생했습니다: {e}"

    return final_response