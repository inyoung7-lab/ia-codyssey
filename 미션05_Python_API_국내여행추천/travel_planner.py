import os
import json
import argparse
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from google import genai


# ==========================================
# 환경 설정
# ==========================================

load_dotenv()

RESULTS_DIR = Path("results")
MODEL_NAME = "gemini-3.5-flash"


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
        raise SystemExit(1)

    return genai.Client(api_key=api_key)


# ==========================================
# 4. Kakao API 키 확인
# ==========================================

def check_kakao_api_key():
    api_key = os.getenv("KAKAO_REST_API_KEY")

    if not api_key:
        print("오류: KAKAO_REST_API_KEY가 설정되지 않았습니다.")
        print(".env 파일에 KAKAO_REST_API_KEY를 설정해주세요.")
        raise SystemExit(1)

    return api_key


# ==========================================
# 5. Gemini 복수 지역 추천
#    보너스 과제 1
# ==========================================

def get_travel_recommendations(client, travel_date):
    prompt = f"""
여행 날짜는 {travel_date}입니다.

이 날짜에 대한민국에서 여행하기 좋은 지역을
서로 다른 3곳 추천해주세요.

반드시 JSON 형식으로만 답변해주세요.
Markdown 코드 블록이나 추가 설명은 작성하지 마세요.

반드시 아래 구조를 지켜주세요.

{{
  "recommended_cities": [
    {{
      "city": "지역명",
      "weather": "해당 시기의 일반적인 날씨 요약",
      "events": [
        "행사 또는 축제 후보 1",
        "행사 또는 축제 후보 2"
      ],
      "reason": "추천 이유를 2~4문장으로 작성"
    }},
    {{
      "city": "지역명",
      "weather": "해당 시기의 일반적인 날씨 요약",
      "events": [
        "행사 또는 축제 후보 1",
        "행사 또는 축제 후보 2"
      ],
      "reason": "추천 이유를 2~4문장으로 작성"
    }},
    {{
      "city": "지역명",
      "weather": "해당 시기의 일반적인 날씨 요약",
      "events": [
        "행사 또는 축제 후보 1",
        "행사 또는 축제 후보 2"
      ],
      "reason": "추천 이유를 2~4문장으로 작성"
    }}
  ]
}}
"""

    last_error = None

    # 최초 요청 + JSON 파싱 실패 시 1회 재시도
    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            text = response.text.strip()
            text = text.replace("```json", "")
            text = text.replace("```", "")
            text = text.strip()

            data = json.loads(text)

            if "recommended_cities" not in data:
                raise ValueError(
                    "recommended_cities 키가 없습니다."
                )

            cities = data["recommended_cities"]

            if not isinstance(cities, list):
                raise ValueError(
                    "recommended_cities는 배열이어야 합니다."
                )

            if len(cities) < 2:
                raise ValueError(
                    "최소 2개 이상의 지역이 필요합니다."
                )

            required_keys = [
                "city",
                "weather",
                "events",
                "reason"
            ]

            for city_data in cities:
                for key in required_keys:
                    if key not in city_data:
                        raise ValueError(
                            f"필수 키가 없습니다: {key}"
                        )

                if not isinstance(city_data["city"], str):
                    raise ValueError(
                        "city는 문자열이어야 합니다."
                    )

                if not isinstance(city_data["weather"], str):
                    raise ValueError(
                        "weather는 문자열이어야 합니다."
                    )

                if not isinstance(city_data["events"], list):
                    raise ValueError(
                        "events는 배열이어야 합니다."
                    )

                if not isinstance(city_data["reason"], str):
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
이전 응답을 JSON으로 파싱할 수 없었습니다.
설명이나 Markdown을 절대 추가하지 말고
recommended_cities 배열과 필수 키만 포함한
올바른 JSON만 다시 출력해주세요.
"""

    raise last_error


# ==========================================
# 6. Kakao Local API 맛집 검색
# ==========================================

def search_restaurants(city, api_key, limit=5):
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
        restaurants.append(
            {
                "name": place.get(
                    "place_name",
                    ""
                ),
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
        )

    return restaurants


# ==========================================
# 7. 캐시 파일 경로
#    보너스 과제 2
# ==========================================

def get_raw_json_path(travel_date):
    return RESULTS_DIR / f"{travel_date}_raw.json"


# ==========================================
# 8. 기존 캐시 확인
# ==========================================

def load_cache(travel_date):
    file_path = get_raw_json_path(travel_date)

    if not file_path.exists():
        return None

    try:
        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        # 새 복수 지역 구조인지 확인
        if (
            "recommendation" not in data
            or "recommended_cities"
            not in data["recommendation"]
        ):
            print(
                "기존 결과 파일은 이전 형식이므로 "
                "캐시를 사용하지 않습니다."
            )
            return None

        print(
            f"캐시 발견: {file_path}"
        )

        return data

    except (
        OSError,
        json.JSONDecodeError,
        TypeError
    ) as error:
        print(
            "캐시 파일을 읽을 수 없어 "
            "새로 API를 호출합니다."
        )
        print(f"캐시 오류: {error}")

        return None


# ==========================================
# 9. 원본 JSON 저장
# ==========================================

def save_raw_json(
    travel_date,
    recommendation,
    restaurants_by_city,
    errors
):
    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    raw_data = {
        "date": travel_date,
        "recommendation": recommendation,
        "restaurants_by_city": restaurants_by_city,
        "errors": errors
    }

    file_path = get_raw_json_path(
        travel_date
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
# 10. 최종 Markdown 리포트 생성
# ==========================================

def generate_final_report(
    client,
    travel_date,
    recommendation,
    restaurants_by_city,
    errors
):
    input_data = {
        "date": travel_date,
        "recommendation": recommendation,
        "restaurants_by_city": restaurants_by_city,
        "errors": errors
    }

    prompt = f"""
아래 JSON 데이터를 이용하여
국내 여행 추천 리포트를 Markdown으로 작성해주세요.

{json.dumps(
    input_data,
    ensure_ascii=False,
    indent=2
)}

여행 추천 지역은 여러 곳입니다.

각 지역마다 반드시 다음 내용을 정리해주세요.

- 추천 지역
- 추천 이유
- 날씨 요약
- 행사/축제
- 맛집 추천
- 1일 일정 제안
  - 오전
  - 오후
  - 저녁

맛집 데이터가 없는 지역은
"데이터 없음"이라고 표시해주세요.

마지막에는 다음 항목을 추가해주세요.

## 오류 요약

errors 배열이 비어 있다면
"발생한 오류 없음"이라고 작성해주세요.

전체 문서의 제목은 다음과 같이 작성해주세요.

# {travel_date} 국내 여행 추천 리포트

Markdown 텍스트만 출력하고
코드 블록으로 감싸지 마세요.
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return response.text.strip()


# ==========================================
# 11. Markdown 저장
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
# 12. 지역별 맛집 검색
# ==========================================

def search_all_cities(
    recommendation,
    kakao_api_key,
    errors
):
    restaurants_by_city = {}

    cities = recommendation[
        "recommended_cities"
    ]

    total = len(cities)

    for index, city_data in enumerate(
        cities,
        start=1
    ):
        city = city_data["city"]

        print()
        print(
            f"  [{index}/{total}] "
            f"{city} 맛집 검색 중..."
        )

        try:
            restaurants = search_restaurants(
                city,
                kakao_api_key,
                limit=5
            )

            restaurants_by_city[
                city
            ] = restaurants

            if restaurants:
                print(
                    f"  - {city}: "
                    f"맛집 {len(restaurants)}곳 "
                    "검색 완료"
                )

                for restaurant_index, restaurant in enumerate(
                    restaurants,
                    start=1
                ):
                    print(
                        f"    {restaurant_index}. "
                        f"{restaurant['name']}"
                    )

            else:
                print(
                    f"  - {city}: 검색 결과 0건"
                )

                errors.append(
                    {
                        "step": "place_search",
                        "city": city,
                        "type": "EMPTY_RESULT",
                        "message": (
                            f"0 results for "
                            f"query={city} 맛집"
                        )
                    }
                )

        except requests.HTTPError as error:
            restaurants_by_city[city] = []

            status_code = (
                error.response.status_code
                if error.response is not None
                else "UNKNOWN"
            )

            error_type = "HTTP_ERROR"

            if status_code in [401, 403]:
                error_type = "AUTH_ERROR"

            print(
                f"  - {city}: "
                f"HTTP 오류 {status_code}"
            )

            print(
                "    맛집은 '데이터 없음'으로 "
                "처리하고 계속 진행합니다."
            )

            errors.append(
                {
                    "step": "place_search",
                    "city": city,
                    "type": error_type,
                    "message": (
                        f"HTTP {status_code}"
                    )
                }
            )

        except requests.RequestException as error:
            restaurants_by_city[city] = []

            print(
                f"  - {city}: "
                "네트워크 오류"
            )

            print(
                "    맛집은 '데이터 없음'으로 "
                "처리하고 계속 진행합니다."
            )

            errors.append(
                {
                    "step": "place_search",
                    "city": city,
                    "type": "NETWORK_ERROR",
                    "message": str(error)
                }
            )

        except Exception as error:
            restaurants_by_city[city] = []

            print(
                f"  - {city}: "
                "알 수 없는 오류"
            )

            print(
                "    맛집은 '데이터 없음'으로 "
                "처리하고 계속 진행합니다."
            )

            errors.append(
                {
                    "step": "place_search",
                    "city": city,
                    "type": "UNKNOWN_ERROR",
                    "message": str(error)
                }
            )

    return restaurants_by_city


# ==========================================
# 13. 추천 지역 출력
# ==========================================

def print_recommended_cities(
    recommendation
):
    cities = recommendation[
        "recommended_cities"
    ]

    print(
        f"복수 지역 추천 완료: "
        f"{len(cities)}곳"
    )

    for index, city_data in enumerate(
        cities,
        start=1
    ):
        print()
        print(
            f"{index}. {city_data['city']}"
        )
        print(
            f"   날씨: "
            f"{city_data['weather']}"
        )

        print("   행사/축제:")

        for event in city_data["events"]:
            print(
                f"   - {event}"
            )

        print(
            f"   추천 이유: "
            f"{city_data['reason']}"
        )


# ==========================================
# 14. 메인 프로그램
# ==========================================

def main():
    args = parse_arguments()

    # 날짜 형식 검증
    if not validate_date(args.date):
        print(
            "오류: 날짜는 YYYY-MM-DD 형식으로 "
            "입력해주세요."
        )

        print(
            '사용법: python travel_planner.py '
            '-date "2026-10-15"'
        )

        return

    print("=" * 55)
    print("국내 여행지 추천 프로그램")
    print("=" * 55)
    print(f"여행 날짜: {args.date}")
    print()

    # --------------------------------------
    # 보너스 2: 캐시 확인
    # --------------------------------------

    cache_data = load_cache(
        args.date
    )

    if cache_data is not None:
        print()
        print(
            "[CACHE] 기존 원본 JSON을 "
            "발견했습니다."
        )

        print(
            "[CACHE] 여행지 추천 및 "
            "Kakao 맛집 API 호출을 "
            "건너뜁니다."
        )

        print()

        recommendation = cache_data[
            "recommendation"
        ]

        restaurants_by_city = (
            cache_data.get(
                "restaurants_by_city",
                {}
            )
        )

        errors = cache_data.get(
            "errors",
            []
        )

        print_recommended_cities(
            recommendation
        )

        # 리포트 재생성을 위해
        # Gemini 클라이언트만 생성
        client = create_gemini_client()

        print()
        print(
            "[3/3] 캐시 데이터로 "
            "최종 리포트 재생성 중(LLM)..."
        )

        try:
            report_text = generate_final_report(
                client,
                args.date,
                recommendation,
                restaurants_by_city,
                errors
            )

            report_path = save_markdown_report(
                args.date,
                report_text
            )

            print("리포트 재생성 완료")
            print()

            print("=" * 55)
            print("캐시 실행 완료!")
            print("=" * 55)

            print(
                "여행지 추천 API: 건너뜀"
            )

            print(
                "Kakao 맛집 API: 건너뜀"
            )

            print(
                f"사용한 캐시: "
                f"{get_raw_json_path(args.date)}"
            )

            print(
                f"여행 리포트: "
                f"{report_path}"
            )

        except Exception as error:
            print(
                "캐시 데이터 기반 리포트 "
                "생성 중 오류가 발생했습니다."
            )

            print(error)

        return

    # --------------------------------------
    # 캐시가 없으면 API 호출
    # --------------------------------------

    errors = []

    client = create_gemini_client()
    kakao_api_key = check_kakao_api_key()

    # --------------------------------------
    # [1/3] Gemini 복수 지역 추천
    # --------------------------------------

    print(
        "[1/3] 복수 여행 지역 추천 "
        "생성 중(LLM)..."
    )

    try:
        recommendation = (
            get_travel_recommendations(
                client,
                args.date
            )
        )

        print_recommended_cities(
            recommendation
        )

    except Exception as error:
        print(
            "Gemini API 호출 또는 "
            "JSON 파싱 중 오류가 발생했습니다."
        )

        print(error)

        return

    # --------------------------------------
    # [2/3] 각 지역 Kakao 맛집 검색
    # --------------------------------------

    print()
    print(
        "[2/3] 지역별 맛집 검색 중"
        "(Kakao Local API)..."
    )

    restaurants_by_city = (
        search_all_cities(
            recommendation,
            kakao_api_key,
            errors
        )
    )

    # --------------------------------------
    # JSON 저장
    # --------------------------------------

    raw_json_path = save_raw_json(
        args.date,
        recommendation,
        restaurants_by_city,
        errors
    )

    print()
    print(
        f"원본 JSON 저장 완료: "
        f"{raw_json_path}"
    )

    # --------------------------------------
    # [3/3] 최종 리포트
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
            restaurants_by_city,
            errors
        )

        report_path = save_markdown_report(
            args.date,
            report_text
        )

        print("리포트 생성 완료")
        print()

        print("=" * 55)
        print("완료!")
        print("=" * 55)

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

        # 리포트 생성 오류도
        # JSON errors에 반영
        save_raw_json(
            args.date,
            recommendation,
            restaurants_by_city,
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