# 미션07 AI 데이터 분석 - 비트코인 트렌드 분석

## 프로젝트 소개

비트코인(BTC-USD)의 시계열 데이터를 Python으로 분석하여
가격 추세, 이동평균, 수익률, 변동성 등의 패턴을 확인하고
데이터 기반 인사이트를 도출하는 프로젝트입니다.

### 🌐 웹 대시보드

Streamlit으로 구현한 Bitcoin(BTC-USD) 시계열 분석 대시보드입니다.
시작일과 종료일을 변경하면서 가격 추세, 이동평균, 일별 수익률,
30일 변동성 등을 직접 탐색할 수 있습니다.

**대시보드 바로 실행:**
[https://inyoung-bitcoin-analysis.streamlit.app](https://inyoung-bitcoin-analysis.streamlit.app)

## 현재 상태

시계열 분석과 시각화, 데이터 기반 인사이트, 보너스 분석 및 대시보드 구현 완료.

## 분석 방법

- 비트코인 가격 추세
- 20일/60일 이동평균
- 일별 수익률
- 30일 변동성

### 보너스 기능

- 기간 선택형 Bitcoin 분석 대시보드
- 7일 주기를 가정한 탐색적 시계열 분해
- 직전 실제값을 이용한 1단계 Naive Forecast 기준선
- MAE/RMSE 예측 오차 평가

## 데이터

- 종목: Bitcoin BTC-USD
- 출처: Yahoo Finance
- 수집 방법: Python `yfinance`
- 기간: 2023-01-01 ~ 2025-12-31
- 데이터 수집 코드: `analysis.ipynb`에 포함

Yahoo Finance 데이터에는 서비스 약관과 재배포 조건이 적용될 수 있습니다. 이 프로젝트는 학습·분석 목적으로 데이터를 사용하며, 데이터나 결과를 제출·배포할 때는 Yahoo Finance와 원 제공자의 최신 이용 조건을 별도로 확인해야 합니다. 이 문서는 특정 라이선스를 추정하지 않습니다.

## 주요 결과

- 전체 가격 변화율: +426.37%
- 최고 일일 상승률: +12.14%
- 최고 일일 하락률: -8.68%
- 최고 30일 변동성: 4.43%

상세한 분석 과정과 외부 자료를 연결한 해석은 [REPORT.md](REPORT.md)를 참고하세요.

## 실행 방법

### 기존 분석 실행

이 프로젝트는 Python 3.13.15에서 검증했으며 Python 3.10 이상 사용을 권장합니다.

1. 저장소 루트에서 가상환경을 생성합니다.

   ```powershell
   python -m venv .venv
   ```

2. 미션07 프로젝트 폴더로 이동합니다.

   ```powershell
   cd 미션07_AI_데이터분석_비트코인
   ```

3. 프로젝트에 필요한 라이브러리를 설치합니다.

   ```powershell
   ..\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

4. 기존 분석과 보너스 분석을 확인하려면 Jupyter Notebook을 실행합니다.

   ```powershell
   ..\.venv\Scripts\python.exe -m jupyter notebook
   ```

5. `analysis.ipynb`를 열고 위에서부터 순서대로 모든 셀을 실행합니다.

### 대시보드 실행

미션07 프로젝트 폴더에서 다음 명령을 실행합니다.

```powershell
..\.venv\Scripts\python.exe -m streamlit run dashboard.py
```

표시되는 로컬 주소를 브라우저에서 열어 분석 기간을 선택할 수 있습니다. 로컬 실행 방법은 배포 URL과 별도로 재현을 위해 유지합니다.

보너스 대시보드는 실제 로컬 실행 화면 스크린샷 세트와 기간 변경 탐색 시나리오로 제출 증빙을 구성했으며, 이 증빙을 그대로 유지하면서 Streamlit Community Cloud 배포 URL도 함께 제공합니다. 자세한 내용은 [REPORT.md](REPORT.md)를 참고하세요.
