import os
from contextlib import redirect_stdout
import io
from prompts import *
from blocks_and_functions import *


def Callout(message,memory):
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
        
        
        elif "추천 관련" in classification_response: 
            metadata_for_yj=[]
            docs = retriever.invoke(message,config=config)
            context = ""
            
            for doc in docs:
                context += doc.page_content + "\n"
                metadata_for_yj.append(doc.metadata)

            #metadata_for_yj = list(set(metadata_for_yj))
            final_response = llm.invoke(
            input = post_rag_inst.format(
                memory = memory,
                input_query = message,
                context = context
            )
            )

        else:

            final_response = llm.invoke(
                input=main_persona.format(input_query=message,memory = memory)
            )
            

    except Exception as e:
        final_response = f"에러가 발생했습니다: {e}"

    return final_response

