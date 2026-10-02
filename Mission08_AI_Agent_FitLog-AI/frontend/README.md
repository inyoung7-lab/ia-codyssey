# FitLog AI 프론트엔드

## 운동시간 추이

브라우저 내장 Canvas로 선 그래프를 그립니다. 외부 라이브러리·CDN·추가 패키지는 없습니다. `/api/data` 응답을 재사용하며 기본 범위는 최근 30일입니다. 최근 7일/30일은 마지막 기록 날짜를 포함한 달력 날짜 기준이고, 전체는 모든 기록을 표시합니다. 휴식일 0분을 보존하며 기록이 없는 날짜는 임의로 채우지 않습니다.

날짜는 오름차순입니다. 마우스 이동·터치 이동 또는 캔버스에서 좌우 방향키로 날짜와 시간을 확인할 수 있습니다. 범위 변경은 추가 API 요청 없이 반영됩니다. 새 기록 저장·새로고침 시 그래프도 갱신되며 선택 범위는 유지됩니다.

HTML / CSS / Vanilla JavaScript 기반 로컬 대시보드입니다. 패키지 설치는 필요하지 않습니다. 로컬 정적 실행은 기존 config.js를 사용하며, Vercel에서는 환경변수로 config.js를 생성하는 빌드를 실행합니다.

프로젝트 루트에서 터미널 두 개로 실행합니다.

```powershell
.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

```powershell
.venv\Scripts\python.exe -m http.server 5500 --bind 127.0.0.1 --directory frontend
```

브라우저에서 http://127.0.0.1:5500 을 엽니다. HTML 파일을 직접 열지 마세요. 종료는 각 터미널에서 Ctrl+C입니다.

정적 서버는 반드시 `frontend` 폴더만 제공해야 합니다. 프로젝트 루트를 제공하면 백엔드 인증 파일이 노출될 수 있습니다.

프론트엔드는 `config.js`의 `API_BASE_URL` 한 곳에 지정된 FastAPI만 GET/POST/PUT/DELETE 요청으로 호출합니다. Firebase에 직접 연결하지 않습니다. CORS는 `http://127.0.0.1:5500`과 `http://localhost:5500`만 허용합니다.

기록 입력은 유효한 날짜, 0~1440분의 정수, 앞뒤 공백을 제외하고 최대 500자의 메모를 받습니다. 저장 성공 후 요약과 최근 기록을 자동 갱신합니다. 같은 날짜는 409로 거부하며 덮어쓰지 않습니다. 연결 실패 시 저장됐을 수도 있으므로 날짜별 조회로 확인한 후 다시 시도하세요.

요약은 전체 기간과 휴식일을 포함합니다. 최근 기록은 데이터의 마지막 날짜부터 7개입니다. 날짜 조회의 404, 빈 데이터, 로딩, 연결 실패를 각각 안내합니다.


## STEP 13 화면 구성

주 화면은 data 요약 → 그래프 → AI 운동 비서 → 이전 대화 → 운동 기록 관리 순서입니다. 기존 workouts 요약·추가·최근 7개·날짜 조회·Ollama 분석은 아래쪽에 별도로 보존합니다. 두 컬렉션은 자동 동기화되지 않으므로 데이터 기준을 화면에서 구분합니다.

- `data.js`: /api/data/summary와 /api/data를 읽고, 10개씩 페이지로 표시합니다. POST 추가, 날짜를 고정한 PUT 수정, 사용자 확인 후 DELETE를 지원합니다. 성공 후 목록·요약·그래프를 갱신하며 그래프 선택 범위는 유지합니다. 204 응답은 JSON 파싱하지 않습니다.
- `chat.js`: 전송 시에만 POST /api/chat을 호출합니다. 대기 중 중복 전송과 대화 전환을 막습니다. 실패 시 질문을 입력창에 남기고 저장 여부가 불명확할 수 있음을 안내합니다. 성공하면 conversation_id를 기억하고 대화 목록을 갱신합니다.
- 이전 대화를 누르면 GET /api/conversations/{id}로 읽습니다. 새 대화는 화면과 현재 ID만 초기화하며 서버 기록을 삭제하지 않습니다. 브라우저 새로고침 후에는 이전 대화 목록에서 다시 선택합니다.
- 모든 메시지·메모·제목은 textContent로 표시하며 HTML로 실행하지 않습니다. frontend에는 API 키·관리자 인증정보를 두지 않습니다.

개발 검증(추가 npm 패키지 불필요, Node.js 테스트 실행에만 필요):
```powershell
node --test tests/frontend.test.cjs
.venv\Scripts\python.exe -m unittest discover -s backend -p "test_*.py" -q
```
프론트엔드 테스트는 가짜 fetch/DOM으로 CRUD·채팅·오류·기록 불러오기·갱신을 검증합니다. 실제 데이터와 GPT에는 쓰기/호출하지 않습니다. 가짜 DOM 검증은 실제 브라우저의 레이아웃·스크린리더 검증을 대체하지 않습니다.


## STEP 14 Bonus

추가 인사이트는 summary.insights를 그대로 표시하며 프론트엔드에서 통계를 재계산하지 않습니다. CSV 다운로드는 export.js에서 현재 불러온 전체 기록으로 생성합니다. UTF-8 BOM과 CSV escaping, 수식 시작 문자 보호를 적용합니다. 빈 데이터나 로딩 중에는 다운로드를 비활성화합니다.

테마는 theme.js와 styles.css가 담당하며 fitlog-theme에 저장합니다. 저장된 선택이 없으면 시스템 테마를 참고합니다. chart.js는 테마 이벤트를 받아 다시 그립니다. JSON 다운로드는 구현하지 않았습니다.

추가 테스트: `node --test tests/frontend.test.cjs tests/bonus.test.cjs`

## Vercel 설정 생성

Root Directory: `Mission08_AI_Agent_FitLog-AI/frontend`
Build Command: `node build-config.js`
Output Directory: `.`

Production의 공개 `API_BASE_URL` 환경변수를 빌드 시 읽어 config.js를 생성합니다. 미설정이나 잘못된 URL은 실패하며 끝 슬래시를 제거합니다. API 키나 Firebase 인증정보는 넣지 않습니다. Preview에도 빌드하려면 해당 범위의 환경변수를 설정하세요. 환경변수 변경 후 새 빌드가 필요합니다.

로컬에서 URL을 변경할 때는 PowerShell에서 `$env:API_BASE_URL`을 원하는 API origin으로 설정하고 프로젝트 루트에서 `node frontend/build-config.js`를 실행합니다. 기존 정적 서버 실행 방법은 같습니다.
