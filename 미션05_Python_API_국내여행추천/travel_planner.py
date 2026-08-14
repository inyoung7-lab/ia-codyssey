import os
import json
import argparse
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from google import genai


# ==========================================
# 환경변수 불러오기
# ==========================================

load_dotenv()

RESULTS_DIR = Path("results")


# ==========================================
# 1. CLI 입력 처리
# ==========================================

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="API를 활용한 국내 여행지 추천 프로그램"
    )

    parser.add_argument(
        "-date",
        "--date",
        required=True,
        help='여행 날짜 (YYYY-MM-DD)'
    )

    return parser.parse_args()


# ==========================================
# 2. 날짜 검증
# ==========================================

def validate_date(date_text):
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
        return True
    except ValueError:
        return False


# ==========================================
# 3. Gemini API 연결
# ==========================================

def create_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("오류: GEMINI_API_KEY가 설정되지 않았습니다.")
        print(".env 파일에 GEMINI_API_KEY를 설정해주세요.")
        raise SystemExit

    return genai.Client(api_key=api_key)


# ==========================================
# 4. 1차 여행지 추천
# ==========================================

def get_travel_recommendation(client, travel_date):
    prompt = f"""
여행 날짜는 {travel_date}입니다.

이 날짜에 대한민국에서 여행하기 좋은 지역 한 곳을 추천해주세요.

반드시 아래 JSON 형식으로만 답변해주세요.
Markdown 코드 블록은 사용하지 마세요.

{{
  "recommended_city": "지역명",
  "weather": "해당 시기의 일반적인 날씨 요약",
  "events": [
    "행사 또는 축제 후보 1",
    "행사 또는 축제 후보 2"
  ],
  "reason": "추천 이유를 2~4문장으로 작성"
}}
"""

    last_error = None

    # 최초 요청 + 실패 시 1회 재시도
    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=prompt
            )

            text = response.text.strip()

            text = text.replace("```json", "")
            text = text.replace("```", "")
            text = text.strip()

            data = json.loads(text)

            required_keys = [
                "recommended_city",
                "weather",
                "events",
                "reason"
            ]

            for key in required_keys:
                if key not in data:
                    raise ValueError(
                        f"필수 키가 없습니다: {key}"
                    )

            if not isinstance(data["recommended_city"], str):
                raise ValueError(
                    "recommended_city는 문자열이어야 합니다."
                )

            if not isinstance(data["weather"], str):
                raise ValueError(
                    "weather는 문자열이어야 합니다."
                )

            if not isinstance(data["events"], list):
                raise ValueError(
                    "events는 배열이어야 합니다."
                )

            if not isinstance(data["reason"], str):
                raise ValueError(
                    "reason은 문자열이어야 합니다."
                )

            return data

        except Exception as error:
            last_error = error

            if attempt == 0:
                print(
                    "LLM JSON 파싱에 실패하여 "
                    "1회 재시도합니다."
                )

                prompt += """
이전 응답을 파싱할 수 없었습니다.
설명이나 Markdown을 추가하지 말고
필수 키만 포함한 올바른 JSON만 출력해주세요.
"""

    raise last_error


# ==========================================
# 5. Kakao Local API 맛집 검색
# ==========================================

def search_restaurants(city, limit=5):
    api_key = os.getenv("KAKAO_REST_API_KEY")

    if not api_key:
        raise ValueError(
            "KAKAO_REST_API_KEY가 설정되지 않았습니다."
        )

    url = (
        "https://dapi.kakao.com/"
        "v2/local/search/keyword.json"
    )

    headers = {
        "Authorization": f"KakaoAK {api_key}"
    }

    params = {
        "query": f"{city} 맛집",
        "size": limit
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    restaurants = []

    for place in data.get("documents", []):
        restaurant = {
            "name": place.get("place_name", ""),

            "address": (
                place.get("road_address_name")
                or place.get("address_name", "")
            ),

            "category": place.get(
                "category_name",
                ""
            ),

            "url": place.get(
                "place_url",
                ""
            ),

            "x": (
                float(place["x"])
                if place.get("x")
                else None
            ),

            "y": (
                float(place["y"])
                if place.get("y")
                else None
            )
        }

        restaurants.append(restaurant)

    return restaurants


# ==========================================
# 6. 원본 JSON 저장
# ==========================================

def save_raw_json(
    travel_date,
    recommendation,
    restaurants,
    errors
):
    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    raw_data = {
        "date": travel_date,
        "recommendation": recommendation,
        "restaurants": restaurants,
        "errors": errors
    }

    file_path = (
        RESULTS_DIR
        / f"{travel_date}_raw.json"
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            raw_data,
            file,
            ensure_ascii=False,
            indent=2
        )

    return file_path


# ==========================================
# 7. 최종 Markdown 리포트 생성
# ==========================================

def generate_final_report(
    client,
    travel_date,
    recommendation,
    restaurants,
    errors
):
    input_data = {
        "date": travel_date,
        "recommendation": recommendation,
        "restaurants": restaurants,
        "errors": errors
    }

    prompt = f"""
아래 JSON 데이터를 사용하여
국내 여행 추천 리포트를 Markdown으로 작성해주세요.

데이터:
{json.dumps(
    input_data,
    ensure_ascii=False,
    indent=2
)}

반드시 아래 항목을 포함해주세요.

# {travel_date} 국내 여행 추천 리포트

## 추천 지역
추천 지역 이름

## 추천 이유
추천 이유 요약

## 날씨 요약
날씨 정보

## 행사/축제
행사 또는 축제 목록

## 맛집 추천
맛집 이름, 주소, 카테고리를 보기 좋게 정리

맛집 데이터가 0건이면 반드시
"데이터 없음"이라고 표시해주세요.

## 1일 일정 제안
오전 / 오후 / 저녁 수준으로 간단하게 작성

## 오류 요약
errors 배열이 비어 있으면
"발생한 오류 없음"이라고 작성해주세요.

Markdown 텍스트만 출력해주세요.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )

    return response.text.strip()


# ==========================================
# 8. Markdown 파일 저장
# ==========================================

def save_markdown_report(
    travel_date,
    report_text
):
    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    file_path = (
        RESULTS_DIR
        / f"{travel_date}_travel_plan.md"
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:
        file.write(report_text)

    return file_path


# ==========================================
# 9. 메인 프로그램
# ==========================================

def main():
    args = parse_arguments()

    if not validate_date(args.date):
        print(
            "오류: 날짜는 YYYY-MM-DD 형식으로 "
            "입력해주세요."
        )

        print(
            '예: python travel_planner.py '
            '-date "2026-10-15"'
        )

        return

    errors = []

    print("국내 여행지 추천 프로그램")
    print(f"여행 날짜: {args.date}")
    print()

    client = create_gemini_client()

    # --------------------------------------
    # [1/3] 1차 LLM 추천
    # --------------------------------------

    print("[1/3] 1차 추천 생성 중(LLM)...")

    try:
        recommendation = (
            get_travel_recommendation(
                client,
                args.date
            )
        )

        print("1차 추천 생성 완료")

        print(
            json.dumps(
                recommendation,
                ensure_ascii=False,
                indent=2
            )
        )

    except Exception as error:
        print(
            "Gemini API 호출 또는 JSON 파싱 중 "
            "오류가 발생했습니다."
        )

        print(error)

        errors.append(
            {
                "step": "recommendation",
                "type": "LLM_ERROR",
                "message": str(error)
            }
        )

        return

    # --------------------------------------
    # [2/3] Kakao 맛집 검색
    # --------------------------------------

    print()
    print(
        "[2/3] 맛집 검색 중"
        "(Kakao Local API)..."
    )

    city = recommendation["recommended_city"]

    try:
        restaurants = search_restaurants(
            city,
            limit=5
        )

        if restaurants:
            print(
                f"맛집 {len(restaurants)}곳 "
                "검색 완료"
            )

            for index, restaurant in enumerate(
                restaurants,
                start=1
            ):
                print()

                print(
                    f"{index}. "
                    f"{restaurant['name']}"
                )

                print(
                    f"   주소: "
                    f"{restaurant['address']}"
                )

                print(
                    f"   카테고리: "
                    f"{restaurant['category']}"
                )

                print(
                    f"   좌표: "
                    f"{restaurant['x']}, "
                    f"{restaurant['y']}"
                )

        else:
            print("검색 결과 0건")

            print(
                "맛집 섹션은 '데이터 없음'으로 "
                "처리하고 계속 진행합니다."
            )

            errors.append(
                {
                    "step": "place_search",
                    "type": "EMPTY_RESULT",
                    "message": (
                        f"0 results for "
                        f"query={city} 맛집"
                    )
                }
            )

    except requests.HTTPError as error:
        restaurants = []

        status_code = (
            error.response.status_code
            if error.response is not None
            else "UNKNOWN"
        )

        print(
            "Kakao Local API HTTP 오류가 "
            "발생했습니다."
        )

        print(
            f"HTTP 상태 코드: "
            f"{status_code}"
        )

        print(
            "맛집 섹션은 '데이터 없음'으로 "
            "처리하고 계속 진행합니다."
        )

        error_type = "HTTP_ERROR"

        if status_code in [401, 403]:
            error_type = "AUTH_ERROR"

        errors.append(
            {
                "step": "place_search",
                "type": error_type,
                "message": (
                    f"HTTP {status_code}"
                )
            }
        )

    except requests.RequestException as error:
        restaurants = []

        print(
            "Kakao Local API 네트워크 오류가 "
            "발생했습니다."
        )

        print(
            "맛집 섹션은 '데이터 없음'으로 "
            "처리하고 계속 진행합니다."
        )

        errors.append(
            {
                "step": "place_search",
                "type": "NETWORK_ERROR",
                "message": str(error)
            }
        )

    except Exception as error:
        restaurants = []

        print(
            "맛집 검색 중 오류가 발생했습니다."
        )

        print(
            "맛집 섹션은 '데이터 없음'으로 "
            "처리하고 계속 진행합니다."
        )

        errors.append(
            {
                "step": "place_search",
                "type": "UNKNOWN_ERROR",
                "message": str(error)
            }
        )

    # --------------------------------------
    # 원본 데이터 JSON 저장
    # --------------------------------------

    raw_json_path = save_raw_json(
        args.date,
        recommendation,
        restaurants,
        errors
    )

    # --------------------------------------
    # [3/3] 최종 리포트 생성
    # --------------------------------------

    print()
    print(
        "[3/3] 최종 리포트 생성 중(LLM)..."
    )

    try:
        report_text = generate_final_report(
            client,
            args.date,
            recommendation,
            restaurants,
            errors
        )

        report_path = save_markdown_report(
            args.date,
            report_text
        )

        print("리포트 생성 완료")
        print()

        print("완료!")
        print(
            f"원본 JSON: "
            f"{raw_json_path}"
        )

        print(
            f"여행 리포트: "
            f"{report_path}"
        )

    except Exception as error:
        errors.append(
            {
                "step": "final_report",
                "type": "LLM_ERROR",
                "message": str(error)
            }
        )

        # 최종 리포트 생성 실패가
        # raw JSON에도 반영되도록 다시 저장
        raw_json_path = save_raw_json(
            args.date,
            recommendation,
            restaurants,
            errors
        )

        print(
            "최종 리포트 생성 중 "
            "오류가 발생했습니다."
        )

        print(error)

        print(
            f"원본 JSON은 저장되었습니다: "
            f"{raw_json_path}"
        )


if __name__ == "__main__":
    main()