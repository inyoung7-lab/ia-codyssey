import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("GEMINI_API_KEY가 설정되지 않았습니다.")
    raise SystemExit

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="gemini-3.5-flash",
    contents="대한민국 국내 여행지 한 곳을 추천해줘. 지역명만 짧게 답해줘."
)

print("Gemini 응답:", response.text)