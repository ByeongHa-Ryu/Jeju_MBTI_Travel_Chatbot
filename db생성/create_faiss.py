import pandas as pd
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document

def create_faiss_db_from_csv(csv_path, output_path):
    """
    CSV 파일을 읽어서 FAISS 데이터베이스로 변환하고 저장합니다.
    
    Args:
        csv_path (str): CSV 파일 경로
        output_path (str): FAISS DB를 저장할 경로
    """
    # CSV 파일 읽기
    df = pd.read_csv(csv_path)
    
    # 임베딩 모델 초기화
    print("임베딩 모델 초기화 중...")
    embeddings = HuggingFaceEmbeddings(
        model_name="jhgan/ko-sroberta-multitask",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # Document 객체 리스트 생성
    print("문서 생성 중...")
    documents = []
    for idx, row in df.iterrows():
        # 검색에 사용될 텍스트 생성
        # 상호명, 주소, 대표메뉴 등을 포함하여 검색 가능하게 함
        text_content = f"""
        음식점명: {row['음식점명']}
        주소: {row['주소']}
        위도: {row['위도']}
        경도: {row['경도']}
        """
        
        # metadata 딕셔너리 생성
        metadata = {
            '음식점명': row['음식점명'],
            '주소': row['주소'],
            '위도': row['위도'],
            '경도': row['경도']
        }
        
        # Document 객체 생성
        doc = Document(
            page_content=text_content,
            metadata=metadata
        )
        documents.append(doc)
    
    # FAISS 데이터베이스 생성
    print("FAISS 데이터베이스 생성 중...")
    db = FAISS.from_documents(documents, embeddings)
    
    # 데이터베이스 저장
    print(f"데이터베이스 저장 중... ({output_path})")
    db.save_local(output_path)
    print("완료!")
    
    return db

import argparse
parser = argparse.ArgumentParser(description='CSV를 FAISS 데이터베이스로 변환')
args = parser.parse_args()
create_faiss_db_from_csv("db생성/test.csv", "faiss_db")

# # 사용 예시
# if __name__ == "__main__":
#     import argparse
    
#     parser = argparse.ArgumentParser(description='CSV를 FAISS 데이터베이스로 변환')
#     parser.add_argument('--csv_path', type=str, required=True, help='입력 CSV 파일 경로')
#     parser.add_argument('--output_path', type=str, required=True, help='출력 FAISS DB 저장 경로')
    
#     args = parser.parse_args()
    
#     try:
#         # FAISS DB 생성
#         db = create_faiss_db_from_csv(args.csv_path, args.output_path)
        
#         # 테스트 검색 수행
#         print("\n테스트 검색 수행 중...")
#         test_query = "제주도 흑돼지"
#         docs = db.similarity_search(test_query, k=3)
        
#         print("\n검색 결과:")
#         for i, doc in enumerate(docs, 1):
#             print(f"\n결과 {i}:")
#             print(f"상호명: {doc.metadata['상호명']}")
#             print(f"주소: {doc.metadata['주소']}")
#             print(f"대표메뉴: {doc.metadata['대표메뉴']}")
            
#     except Exception as e:
#         print(f"에러 발생: {e}")