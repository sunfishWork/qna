import requests
import json

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
        print("DeepSeek API Response:", result["response"])

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

text = """
  {
    "id": "23501-i80_chunk_1",
    "document_id": "23501-i80",
    "chunk_id": 1,
    "text": "Contents Foreword 22 1 Scope 23 2 References 23 3 Definitions and abbreviations 30 31 Definitions 30 32 Abbreviations 37 4 Architecture model and concepts 41 41 General concepts 41 42 Architecture reference model 41 421 General 41 422 Network Functions and entities 42 423 Non-roaming reference architecture 43 424 Roaming reference architectures 46 425 Data Storage architectures 50 425a Radio Capabilities Signalling optimisation 52 426 Service-based interfaces 52 427 Reference points 53 428 Support of non-3GPP access 56 4280 General 56 4281 General Concepts to Support Trusted and Untrusted Non-3GPP Access 56 4281A General Concepts to support Wireline Access 57 4282 Architecture Reference Model for Trusted and Untrusted Non-3GPP Accesses 58 42821 Non-roaming Architecture 58 42822 LBO Roaming Architecture 59 42823 Home-routed Roaming Architecture 62 4283 Reference Points for Non-3GPP",
    "metadata": {
      "source": "0_spec/23501-i80.docx"
    }
  }
"""

print('================')
print(generate_qna(text))