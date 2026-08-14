# 국내 여행지 추천 프로그램

Python과 외부 API를 활용하여 여행 날짜에 맞는 국내 여행지를 추천하고,
추천 지역의 맛집 정보를 검색한 뒤 최종 여행 리포트를 생성하는 프로그램입니다.

## 1. 프로젝트 개요

사용자가 여행 날짜를 입력하면 다음 과정을 자동으로 수행합니다.

1. 입력한 날짜 형식 검증
2. Gemini API를 이용한 국내 여행지 추천
3. 추천 지역의 날씨 특징 및 행사 정보 생성
4. Kakao Local API를 이용한 주변 맛집 검색
5. 수집한 정보를 JSON 형식으로 저장
6. 최종 국내 여행 추천 리포트를 Markdown 파일로 생성

전체적인 흐름은 다음과 같습니다.

`여행 날짜 입력 → 날짜 검증 → Gemini 여행지 추천 → Kakao 맛집 검색 → JSON 저장 → Markdown 리포트 생성`

---

## 2. 사용 기술

- Python 3.14
- Google Gemini API
- Kakao Local API
- requests
- python-dotenv
- JSON
- Markdown
- Git / GitHub

---

## 3. 주요 파일

### `travel_planner.py`

프로젝트의 메인 프로그램입니다.

여행 날짜를 입력받아 Gemini API와 Kakao Local API를 호출하고,
최종 결과를 JSON 및 Markdown 파일로 저장합니다.

### `gemini_test.py`

Gemini API가 정상적으로 연결되는지 확인하기 위한 테스트 프로그램입니다.

### `.env`

API 키를 저장하는 환경 변수 파일입니다.

보안을 위해 GitHub에는 업로드하지 않습니다.

### `.gitignore`

`.env`, Python 캐시 파일 및 실행 결과 폴더 등
Git에 포함하지 않을 파일을 관리합니다.

### `results/`

프로그램 실행 후 생성되는 결과 파일이 저장됩니다.

예시:

- `2026-10-15_raw.json`
- `2026-10-15_travel_plan.md`

### `evidence/`

프로젝트 구현 및 테스트 과정의 증빙 이미지가 저장됩니다.

---

## 4. 프로그램 실행 방법

프로젝트 폴더에서 다음 명령어를 실행합니다.

```bash
python travel_planner.py --date "2026-10-15"