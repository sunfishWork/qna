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


def save_text_to_json(text: str, output_path: str, out_folder: str, source_file: str, chunk_size: int = 1000) -> None:
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


def process_document(input_path: str, out_folder: str, chunk_size: int = 1000) -> None:
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
    output_file_name = os.path.join(out_folder, "output.txt")  # Base output file name
    # save_text_to_file(cleaned_text, output_file_name, out_folder, chunk_size)
    save_text_to_json(cleaned_text, output_folder, output_folder, input_file, chunk_size=1000)



# Example usage
if __name__ == "__main__":
    from_folder = "0_spec"  # 'qnaspec' 폴더 지정
    to_folder = "1_chunk"  # 결과 저장할 상위 폴더 지정

    # 'from' 폴더 내 모든 .pdf 및 .docx 파일 찾기
    if not os.path.exists(from_folder):
        print(f"Error: The folder '{from_folder}' does not exist.")
        exit()

    files = [f for f in os.listdir(from_folder) if f.lower().endswith(('.pdf', '.docx'))]

    if not files:
        print("No PDF or DOCX files found in 'from' folder.")
        exit()

    for file in files:
        input_file = os.path.join(from_folder, file)

        # Extract the base name of the input file without extension
        base_name = os.path.splitext(os.path.basename(input_file))[0]

        # Create an output folder inside '1_chunk' with the same name as the original file
        output_folder = os.path.join(to_folder, base_name)
        os.makedirs(output_folder, exist_ok=True)
        print(f"Processing '{file}' and saving output to: {output_folder}")

        process_document(input_file, output_folder)
