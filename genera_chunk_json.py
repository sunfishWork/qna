import os
import re
import fitz  # PyMuPDF
import spacy
from docx import Document
import json


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from a DOCX file."""
    doc = Document(file_path)
    return '\n'.join([para.text for para in doc.paragraphs])


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    text = ""
    doc = fitz.open(file_path)
    for page in doc:
        text += page.get_text("text") + "\n"
    return text


def clean_text(text: str) -> str:
    # Replace newline and tab characters with spaces
    cleaned = text.replace("\n", " ").replace("\t", " ")

    # Remove URLs (http/https links)
    cleaned = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '',
                     cleaned)
    # Remove email addresses
    cleaned = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', cleaned)

    """Clean the extracted text by removing special characters and normalizing whitespace."""
    cleaned = re.sub(r'[^\w\s-]', '', cleaned)  # Remove special characters
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()  # Normalize spaces

    return cleaned


# def clean_text(text):
#     """Clean and preprocess the extracted text by removing irrelevant elements."""
#     # Remove special characters (keep basic punctuation)
#     cleaned_text = re.sub(r'[^a-zA-Z0-9 .,!?;:()\'"-]', ' ', text)
#
#     # Remove URLs (http/https links)
#     cleaned_text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '',
#                           cleaned_text)
#
#     # Remove email addresses
#     cleaned_text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', cleaned_text)
#
#     # Remove extra punctuation (e.g., multiple exclamation points or question marks)
#     cleaned_text = re.sub(r'([!?.]){2,}', r'\1', cleaned_text)
#
#     # Remove numbers (optional: uncomment if you want to remove all numbers)
#     # cleaned_text = re.sub(r'\d+', '', cleaned_text)
#
#     # Convert to lowercase (optional: uncomment if you want case-insensitive text)
#     # cleaned_text = cleaned_text.lower()
#
#     # Strip leading and trailing whitespace
#     cleaned_text = cleaned_text.strip()
#
#     return cleaned_text


# Load the spaCy language model
nlp = spacy.load("en_core_web_sm")
nlp.max_length = 3_000_000  # spaCy 최대 길이 확장


# def save_text_to_file(text: str, output_path: str, out_folder: str, chunk_size: int = 1000) -> None:
#     """Save cleaned text to multiple chunked files without splitting sentences."""
#     nlp.max_length = 3_000_000  # 3M characters로 확장 (필요하면 더 증가 가능)
#     doc = nlp(text)
#     sentences = [sent.text for sent in doc.sents]
#
#     current_chunk = []
#     current_length = 0
#     chunk_number = 1  # 청크 번호 초기화
#
#     for sentence in sentences:
#         estimated_length = current_length + len(sentence) + 1
#
#         if estimated_length > chunk_size:
#             # Save current chunk
#             save_chunk(chunk_number, current_chunk, out_folder, output_path)
#
#             # Start a new chunk
#             chunk_number += 1
#             current_chunk = [sentence]
#             current_length = len(sentence) + 1
#         else:
#             current_chunk.append(sentence)
#             current_length = estimated_length
#
#     # Save the last chunk
#     if current_chunk:
#         save_chunk(chunk_number, current_chunk, out_folder, output_path)
#
#
# def save_chunk(chunk_number, current_chunk, out_folder, output_path):
#     chunk_text = ' '.join(current_chunk)
#     chunk_file = os.path.join(out_folder, f"{os.path.basename(output_path).split('.')[0]}_{chunk_number}.txt")
#     with open(chunk_file, 'w', encoding='utf-8') as f:
#         f.write(chunk_text)
#     print(f"Saved: {chunk_file}")


def save_text_to_json(text: str, source_file: str, out_folder: str, chunk_size: int = 1000) -> None:
    """Save cleaned text as JSON format without splitting sentences."""
    doc = nlp(text)
    sentences = [sent.text for sent in doc.sents]

    current_chunk = []
    current_length = 0
    chunk_number = 1  # 청크 번호 초기화
    json_data = []  # JSON 데이터 저장 리스트

    document_id = os.path.splitext(os.path.basename(source_file))[0]  # 파일명에서 확장자 제거

    for sentence in sentences:
        estimated_length = current_length + len(sentence) + 1

        if estimated_length > chunk_size:
            # Save current chunk
            json_data.append(create_chunk_dict(document_id, chunk_number, current_chunk, source_file))

            # Start a new chunk
            chunk_number += 1
            current_chunk = [sentence]
            current_length = len(sentence) + 1
        else:
            current_chunk.append(sentence)
            current_length = estimated_length

    # Save the last chunk
    if current_chunk:
        json_data.append(create_chunk_dict(document_id, chunk_number, current_chunk, source_file))

    # JSON 파일 저장
    json_file_path = os.path.join(out_folder, f"{document_id}.json")
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(json_data, json_file, ensure_ascii=False, indent=2)

    print(f"Saved JSON: {json_file_path}")


def create_chunk_dict(document_id, chunk_number, chunk_sentences, source_file):
    """JSON 포맷에 맞게 청크 데이터를 딕셔너리 형태로 변환."""
    return {
        "id": f"{document_id}_chunk_{chunk_number}",
        "document_id": document_id,
        "chunk_id": chunk_number,
        "text": " ".join(chunk_sentences),
        "metadata": {
            "source": source_file,
        }
    }


def process_document(input_path: str, out_folder: str) -> None:
    """Process the document and save cleaned text in chunks."""
    # Extract text based on file type
    if input_path.lower().endswith('.docx'):
        text = extract_text_from_docx(input_path)
    elif input_path.lower().endswith('.pdf'):
        text = extract_text_from_pdf(input_path)
    else:
        raise ValueError("Unsupported file format. Only .DOCX and .PDF are supported.")

    # Clean the text
    cleaned_text = clean_text(text)

    # Create output folder if it doesn't exist
    os.makedirs(out_folder, exist_ok=True)

    # Save text in chunks
    # output_file_name = os.path.join(out_folder, "output.txt")  # Base output file name
    # save_text_to_file(cleaned_text, output_file_name, out_folder, chunk_size)
    save_text_to_json(cleaned_text, input_file, out_folder, chunk_size=1000)


import json
import requests
import time

# DeepSeek-R1:32B 모델을 사용하는 Ollama API 엔드포인트
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "deepseek-r1:32b"


def generate_qna(text):
    """LLM을 사용하여 주어진 텍스트에서 QnA를 생성"""
    prompt = f"""
    Generate QnA pairs in **strict JSON format** based on the following text. 
    Do **NOT** add explanations, comments, or any additional text. 
    Only return the JSON array.

    Text:
    {text}

    Output Format (JSON array only):
    ```json
    [
      {{"question": "What is the main topic of the document?", "answer": "This document discusses machine learning."}},
      {{"question": "What is machine learning?", "answer": "Machine learning is a method of analyzing data and automatically building predictive models."}}
    ]
    ```
    """

    payload = {
        "model": "deepseek-r1:7b",
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post("http://localhost:11434/api/generate", json=payload)
        response.raise_for_status()
        result = response.json()

        # API 응답 출력하여 확인
        # print("DeepSeek API Response:", result["response"])

        # JSON 데이터만 추출하기 위해 <think> 태그 및 코드 블록 제거
        raw_text = result["response"].strip()
        raw_text = raw_text.replace("<think>", "").replace("</think>", "").strip()

        # JSON 코드 블록이 있을 경우 제거
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[-1].split("```")[0].strip()

        return json.loads(raw_text)  # JSON 변환
    except Exception as e:
        print(f"Error generating QnA: {e}")
        return []  # 실패 시 빈 리스트 반환



if __name__ == "__main__":
    # ==============================
    # Create Chunk json files
    # ==============================
    # from_folder = "0_spec"
    # to_folder = "1_chunk"
    #
    # # 'from' 폴더 내 모든 .pdf 및 .docx 파일 찾기
    # if not os.path.exists(from_folder):
    #     print(f"Error: The folder '{from_folder}' does not exist.")
    #     exit()
    #
    # files = [f for f in os.listdir(from_folder) if f.lower().endswith(('.pdf', '.docx'))]
    #
    # if not files:
    #     print("No PDF or DOCX files found in 'from' folder.")
    #     exit()
    #
    # output_folder = os.path.join(to_folder)
    # for file in files:
    #     input_file = os.path.join(from_folder, file)
    #
    #     # Extract the base name of the input file without extension
    #     base_name = os.path.splitext(os.path.basename(input_file))[0]
    #
    #     os.makedirs(output_folder, exist_ok=True)
    #     print(f"Processing '{file}' and saving output to: {output_folder}")
    #
    #     process_document(input_file, output_folder)

    # ==============================
    # Create QnA json files
    # ==============================
    from_folder = "1_chunk"
    to_folder = "2_qna"

    # 'from' 폴더 내 모든 .pdf 및 .docx 파일 찾기
    if not os.path.exists(from_folder):
        print(f"Error: The folder '{from_folder}' does not exist.")
        exit()

    files = [f for f in os.listdir(from_folder) if f.lower().endswith('.json')]

    if not files:
        print("No json files found in 'from' folder.")
        exit()

    for file in files:
        input_file = os.path.join(from_folder, file)

        # Extract the base name of the input file without extension
        base_name = os.path.splitext(os.path.basename(input_file))[0]

        # Create an output folder inside '2_qna' with the same name as the original file
        # output_folder = os.path.join(to_folder, base_name)
        os.makedirs(to_folder, exist_ok=True)
        print(f"Processing '{file}' and saving output to: {to_folder}")

        # JSON 파일 읽기
        with open(input_file, 'r', encoding='utf-8') as f:
            chunk_data = json.load(f)

        qna_data = []

        for chunk in chunk_data:
            chunk_id = chunk["id"]
            text = chunk["text"]
            source = chunk["metadata"]["source"]

            # LLM을 호출하여 QnA 생성
            qna_list = generate_qna(text)
            print(f"from Deekseek: ", qna_list)

            for idx, qna in enumerate(qna_list):
                qna_data.append({
                    "id": f"{chunk_id}_qna_{idx + 1}",
                    "document_id": base_name,
                    "chunk_id": chunk_id,
                    "question": qna["question"],
                    "answer": qna["answer"],
                    "metadata": {
                        "source": source
                    }
                })

            # time.sleep(1)  # API 과부하 방지를 위한 딜레이

        # QnA JSON 저장
        output_file = os.path.join(to_folder, f"{base_name}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(qna_data, f, ensure_ascii=False, indent=2)

        print(f"Saved QnA JSON: {output_file}")