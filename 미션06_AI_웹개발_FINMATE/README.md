# FINMATE AI

FINMATE AI는 투자 초보자가 기업과 투자 정보를 쉽게 이해할 수 있도록 돕는 AI 투자 학습 웹 서비스입니다. 사용자가 기업명을 입력하면 Gemini가 기업 소개, 주요 사업, 강점, 위험 요소 등을 한국어로 설명합니다.

특정 종목의 매수·매도를 추천하거나 수익을 보장하는 서비스가 아니며, AI 답변은 투자 학습과 정보 제공 목적으로만 사용합니다.

## 1. 배포 서비스

- 서비스명: FINMATE AI
- Production URL: <https://finmate-ai-gold.vercel.app>
- 배포 환경: Vercel Production
- 소스 관리: Git / GitHub

## 2. 실제 구현 기능

### 화면 구성

- 홈: 서비스 핵심 메시지와 AI 기업 분석 시작 버튼
- 투자 학습: `주식이란?`, `PER · PBR`, `투자 위험`을 소개하는 정적 학습 카드
- AI 기업 분석: 기업명 입력, 분석 요청, 상태 및 결과 표시
- 서비스 소개: 서비스 목적과 투자 유의 문구
- 상단 메뉴를 통한 섹션 이동과 라이트/다크 모드 전환

### AI 기업 분석

AI에 전달하는 사용자 입력은 **기업명 한 가지**입니다.

예시 입력:

- 삼성전자
- Apple
- NVIDIA

Gemini 프롬프트는 다음 형식의 분석을 요청합니다.

- 기업 소개
- 주요 사업
- 강점
- 위험 요소
- 초보자 한줄 정리

답변은 투자 초보자가 이해하기 쉬운 한국어로 작성하도록 요청하며, 매수·매도 권유, 수익 보장 표현, 확인되지 않은 숫자, 실시간 주가를 알고 있다고 가정한 설명을 제한합니다.

## 3. AI 요청과 응답 흐름

```text
사용자 기업명 입력
        ↓
HTML form 제출
        ↓
JavaScript fetch('/api/analyze')
        ↓
Vercel Serverless Function
        ↓
Python api/analyze.py
        ↓
Gemini API
        ↓
Python이 JSON 응답 반환
        ↓
JavaScript가 분석 결과를 화면에 출력
```

프론트엔드는 다음과 같이 JSON 본문을 담은 `POST` 요청을 보냅니다.

```json
{
  "company": "삼성전자"
}
```

정상 처리 시 Python 백엔드는 다음 필드를 담은 JSON을 반환하고, JavaScript는 `analysis` 값을 화면에 표시합니다.

```json
{
  "company": "삼성전자",
  "analysis": "AI가 생성한 기업 분석 내용",
  "model": "사용한 Gemini 모델명"
}
```

## 4. 입력 검증, 로딩 및 실패 처리

### 빈 입력

- 입력창에 HTML `required` 속성을 적용해 빈 값 제출 시 브라우저의 필수 입력 안내가 표시됩니다.
- 공백만 입력한 경우를 포함해 JavaScript에서도 값을 `trim()`한 뒤 다시 검사합니다.
- 프론트엔드와 Python 백엔드 모두 기업명이 100자를 넘지 않는지 검사합니다.

### 분석 진행 상태

- 상태 영역에 `AI가 기업 정보를 분석하고 있습니다...`를 표시합니다.
- 결과 영역에도 분석 중 안내를 표시합니다.
- 처리 중 버튼을 비활성화하고 문구를 `분석 중...`으로 바꾸어 중복 요청을 방지합니다.
- 성공 또는 실패 후 버튼을 다시 활성화합니다.

### API 및 네트워크 오류

- 네트워크가 끊기거나 `fetch` 자체가 실패하면 `네트워크 연결 또는 AI 서비스에 문제가 발생했습니다. 잠시 후 다시 시도해주세요.`를 사용자 화면에 표시합니다.
- 인증, 요청 한도, 응답 지연, 서버 오류, 빈 AI 결과, 잘못된 JSON 응답도 기술적인 오류 원문 대신 상황별 한국어 안내 문구로 처리합니다.
- 오류가 발생한 경우 결과 영역에는 `분석 결과를 불러오지 못했습니다.`를 표시합니다.
- Python 백엔드는 잘못된 요청, 누락된 환경 변수, Gemini HTTP/네트워크/시간 초과 오류, 응답 파싱 오류에 대해 JSON 오류 응답과 코드에서 정한 HTTP 상태를 반환합니다.

## 5. 기술 구성과 파일 역할

| 구분 | 기술 및 역할 |
|---|---|
| HTML | 단일 페이지의 홈, 투자 학습, AI 분석, 서비스 소개 영역과 기업명 입력 form 구성 |
| CSS | 색상, 레이아웃, 카드, 상태 표시, 다크 모드 및 반응형 화면 구성 |
| JavaScript | 메뉴 이동, 테마 전환, 입력 검사, 로딩/오류 상태, `/api/analyze` 호출, 결과 출력 |
| Python | 요청 JSON과 기업명을 검사하고 Gemini API를 호출한 뒤 성공 또는 오류 JSON 반환 |
| Vercel Serverless Functions | `api/analyze.py`를 서버리스 API로 실행 |
| Gemini API | 기업명을 바탕으로 초보자용 기업 분석 내용 생성 |
| Git / GitHub | 소스 버전 관리 |
| Vercel | 정적 프론트엔드, Python API, Production 서비스 배포 |

프론트엔드는 별도 프레임워크 없이 HTML, CSS, Vanilla JavaScript로 구현했습니다. Python 백엔드는 표준 라이브러리만 사용하므로 현재 `requirements.txt`에 추가 패키지가 없습니다.

## 6. 프로젝트 구조

```text
미션06_AI_웹개발_FINMATE/
├── api/
│   └── analyze.py
├── css/
│   └── style.css
├── evidence/
│   ├── 01_main_page.png
│   ├── 02_learning_page.png
│   ├── 03_ai_analysis_page.png
│   ├── 04_vercel_production_deployment.png
│   ├── 05_vercel_ai_analysis_success.png
│   ├── 06_env_git_security_check.png
│   ├── 07_mobile_responsive.png
│   ├── 08_debugging_process.png
│   ├── 09_ai_coding_tool_debugging.png
│   ├── 10_empty_input_validation.png
│   └── 11_api_error_handling.png
├── images/               # 현재 정적 이미지 파일 없음
├── js/
│   └── app.js
├── .env                 # 로컬 전용, Git 제외
├── .gitignore
├── index.html
├── README.md
├── requirements.txt
├── vercel.json
└── 서비스_기획서.md
```

## 7. 환경 변수와 API Key 보안

Python은 코드에 Key를 직접 넣지 않고 실행 환경의 `GEMINI_API_KEY`를 읽습니다.

- 로컬 환경: `.env`에 `GEMINI_API_KEY` 설정
- 배포 환경: Vercel Environment Variables의 Production 환경에 `GEMINI_API_KEY` 설정
- Git 보안: `.gitignore`에서 `.env`, `.env.local`, `.env.*` 제외
- 프론트엔드 보호: 브라우저는 Gemini API를 직접 호출하지 않고 `/api/analyze`만 호출
- 로그 보호: 백엔드 오류 로그에 API Key 값을 출력하지 않음

`.env`는 로컬에만 존재하며 Git 추적 대상이 아닙니다. 실제 Key 값은 문서, JavaScript, Python 코드에 기록하지 않습니다.

## 8. 실행 및 Vercel 배포

### 로컬 확인

1. 로컬 `.env`에 `GEMINI_API_KEY`를 설정합니다.
2. Vercel CLI가 설치된 환경에서 프로젝트 폴더를 엽니다.
3. `vercel dev`로 정적 화면과 Python Serverless Function을 함께 실행합니다.

### Production 배포

1. Git/GitHub에서 제출할 소스를 관리합니다.
2. Vercel 프로젝트의 Environment Variables에 `GEMINI_API_KEY`를 Production용 민감 정보로 등록합니다.
3. 프로젝트 루트에서 `vercel --prod`를 실행합니다.
4. 배포 완료 후 Production alias인 <https://finmate-ai-gold.vercel.app>에서 화면과 AI 분석을 확인합니다.

`vercel.json`은 정적 HTML/CSS/JavaScript와 `api/*.py`를 각각 정적 리소스와 Python Serverless Function으로 빌드하고, `/api/analyze` 요청을 `/api/analyze.py`로 연결합니다.

## 9. 반응형 구현

CSS Media Query를 사용해 화면 폭에 따라 레이아웃을 조정했습니다.

- 데스크톱: 메뉴와 3열 학습 카드, 가로형 입력창과 버튼 표시
- 작은 화면: 상단 메뉴 링크 숨김, 학습 카드 1열 배치, 입력창과 버튼 세로 배치
- 제목 크기와 자간: 900px 및 600px 구간에서 추가 조정

실제 동작 확인은 데스크톱 화면과 Chrome DevTools의 400 × 857 모바일 화면에서 완료했습니다.

## 10. 증빙 자료

| 번호 | 파일 | 증명하는 내용 |
|---:|---|---|
| 01 | `01_main_page.png` | Vercel에 표시된 FINMATE AI 홈 화면, 상단 메뉴, 핵심 문구, AI 분석 시작 버튼 |
| 02 | `02_learning_page.png` | 주식, PER·PBR, 투자 위험으로 구성된 투자 학습 카드와 데스크톱 레이아웃 |
| 03 | `03_ai_analysis_page.png` | 기업명 하나를 입력하는 AI 기업 분석 form, 분석 버튼, 상태 및 결과 표시 영역 |
| 04 | `04_vercel_production_deployment.png` | `vercel --prod` 배포 성공, Production 배포 주소와 `finmate-ai-gold.vercel.app` alias |
| 05 | `05_vercel_ai_analysis_success.png` | 배포 서비스에서 `삼성전자` 입력 후 분석 완료 상태와 기업 소개·주요 사업·강점 결과 출력 |
| 06 | `06_env_git_security_check.png` | Vercel Production의 `GEMINI_API_KEY`가 Sensitive로 등록된 상태와 `.env`의 Git 제외 확인 |
| 07 | `07_mobile_responsive.png` | Chrome DevTools 400 × 857 화면에서 메뉴 축소, 입력창과 버튼의 세로 배치 등 모바일 반응형 동작 |
| 08 | `08_debugging_process.png` | 로컬 Vercel 실행 중 Python 경로 오류 로그를 확인하고 수정 후 `vercel dev`를 다시 실행한 과정 |
| 09 | `09_ai_coding_tool_debugging.png` | AI 코딩 도구를 이용해 로컬 502 오류 원인과 Vercel/Python 구성 수정 방향을 분석한 과정 |
| 10 | `10_empty_input_validation.png` | 기업명을 입력하지 않았을 때 브라우저가 필수 입력 안내를 표시하는 동작 |
| 11 | `11_api_error_handling.png` | DevTools 오프라인 상태에서 `/api/analyze` 요청이 실패하고 사용자용 네트워크 오류 문구와 결과 대체 문구가 표시되는 동작 |

## 11. 검증 완료 범위

- 홈, 투자 학습, AI 기업 분석, 서비스 소개 화면 표시
- 기업명 입력 후 `/api/analyze` 요청
- Vercel Serverless Function에서 Gemini API 호출
- AI 분석 JSON 수신 및 화면 출력
- 빈 입력 차단, 로딩 표시, 버튼 중복 요청 방지
- 오프라인 네트워크 오류 안내
- 데스크톱 및 모바일 반응형 화면
- `.env` Git 제외와 Vercel 환경 변수 설정
- Vercel Production 배포

## 12. 이용 시 주의사항

AI가 생성한 내용은 최신 기업 정보와 다를 수 있습니다. 실제 투자 결정을 내릴 때에는 기업의 공식 자료와 최신 정보를 별도로 확인해야 하며, 모든 투자 판단과 책임은 사용자에게 있습니다.
