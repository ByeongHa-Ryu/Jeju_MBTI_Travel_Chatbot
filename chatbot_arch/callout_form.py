import os
from contextlib import redirect_stdout
import io
from chatbot_arch.prompts import *
# from blocks_and_functions import *
import streamlit as st
from streamlit_folium import folium_static
import google.generativeai as genai
from langchain.vectorstores import FAISS
from streamlit_folium import st_folium
import os
from contextlib import redirect_stdout
import io
from chatbot_arch.blocks_and_functions import *



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
                final_response, _, _ = process_recommendation(message, user_mbti, month)
                return final_response
                
            except Exception as e:
                return f"맛집 추천 처리 중 에러가 발생했습니다: {e}"
            
        elif "부가 질문" in classification_response:
            restaurants_state, tourist_spots_state = state()
            final_response = llm.invoke(
                input=question_inst.format(
                    input_query = message,
                    memory = memory,
                    restaurants = restaurants_state,
                    tour = tourist_spots_state
                    )
            )
        
        else:
            final_response = llm.invoke(
                input=main_persona.format(input_query=message,memory = memory)
            )

    except Exception as e:
        final_response = f"에러가 발생했습니다: {e}"

    return final_response