# 미션07 AI 데이터 분석 - 비트코인 트렌드 분석

## 프로젝트 소개

비트코인(BTC-USD)의 시계열 데이터를 Python으로 분석하여
가격 추세, 이동평균, 수익률, 변동성 등의 패턴을 확인하고
데이터 기반 인사이트를 도출하는 프로젝트입니다.

## 현재 상태

시계열 분석과 시각화, 데이터 기반 인사이트 및 결론 작성 완료.

## 분석 방법

- 비트코인 가격 추세
- 20일/60일 이동평균
- 일별 수익률
- 30일 변동성

## 데이터

- 종목: Bitcoin BTC-USD
- 출처: Yahoo Finance
- 수집 방법: Python `yfinance`
- 기간: 2023-01-01 ~ 2025-12-31
- 데이터 수집 코드: `analysis.ipynb`에 포함

## 주요 결과

- 전체 가격 변화율: +426.37%
- 최고 일일 상승률: +12.14%
- 최고 일일 하락률: -8.68%
- 최고 30일 변동성: 4.43%

상세한 분석 과정과 외부 자료를 연결한 해석은 [REPORT.md](REPORT.md)를 참고하세요.

## 실행 방법

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

4. Jupyter Notebook을 실행합니다.

   ```powershell
   ..\.venv\Scripts\python.exe -m jupyter notebook
   ```

5. `analysis.ipynb`를 열고 위에서부터 순서대로 모든 셀을 실행합니다.
