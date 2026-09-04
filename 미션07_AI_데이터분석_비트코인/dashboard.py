from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st


PROJECT_DIR = Path(__file__).resolve().parent
CSV_PATH = PROJECT_DIR / "data" / "bitcoin_2023_2025.csv"


def load_and_prepare_data(csv_path: Path = CSV_PATH) -> pd.DataFrame:
    """CSV를 읽고 전체 기간을 기준으로 시계열 지표를 계산한다."""
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {csv_path.name}")

    data = pd.read_csv(csv_path)
    required_columns = {"Date", "Close"}
    missing_columns = required_columns.difference(data.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"필수 컬럼이 없습니다: {missing}")

    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    data["Close"] = pd.to_numeric(data["Close"], errors="coerce")
    if data.empty:
        raise ValueError("CSV에 데이터가 없습니다.")
    if data["Date"].isna().any():
        raise ValueError("Date 컬럼에 날짜로 변환할 수 없는 값이 있습니다.")
    if data["Close"].isna().any():
        raise ValueError("Close 컬럼에 숫자로 변환할 수 없는 값이 있습니다.")

    data = data.sort_values("Date").reset_index(drop=True)
    data["MA20"] = data["Close"].rolling(window=20, min_periods=20).mean()
    data["MA60"] = data["Close"].rolling(window=60, min_periods=60).mean()
    data["Daily_Return"] = data["Close"].pct_change(fill_method=None) * 100
    data["Volatility_30"] = data["Daily_Return"].rolling(
        window=30, min_periods=30
    ).std()
    return data


def filter_by_date(
    data: pd.DataFrame, start_date: object, end_date: object
) -> pd.DataFrame:
    """시작일과 종료일을 모두 포함해 데이터를 선택한다."""
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    if start > end:
        raise ValueError("시작일은 종료일보다 늦을 수 없습니다.")

    mask = data["Date"].between(start, end, inclusive="both")
    return data.loc[mask].copy()


def calculate_summary(data: pd.DataFrame) -> dict[str, float | None]:
    """선택 기간의 요약 지표를 계산하며 값이 없으면 None을 반환한다."""
    if data.empty:
        return {
            "start_close": None,
            "end_close": None,
            "change_pct": None,
            "max_return": None,
            "min_return": None,
            "mean_return": None,
            "mean_volatility": None,
        }

    start_close = float(data["Close"].iloc[0])
    end_close = float(data["Close"].iloc[-1])
    daily_returns = data["Daily_Return"].dropna()
    volatility = data["Volatility_30"].dropna()

    return {
        "start_close": start_close,
        "end_close": end_close,
        "change_pct": (end_close / start_close - 1) * 100
        if start_close != 0
        else None,
        "max_return": float(daily_returns.max()) if not daily_returns.empty else None,
        "min_return": float(daily_returns.min()) if not daily_returns.empty else None,
        "mean_return": float(daily_returns.mean()) if not daily_returns.empty else None,
        "mean_volatility": float(volatility.mean()) if not volatility.empty else None,
    }


def format_metric(value: float | None, suffix: str = "") -> str:
    if value is None or not np.isfinite(value):
        return "N/A"
    return f"{value:,.2f}{suffix}"


def format_date_axis(axis: plt.Axes) -> None:
    locator = mdates.AutoDateLocator(minticks=3, maxticks=8)
    axis.xaxis.set_major_locator(locator)
    axis.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
    axis.grid(alpha=0.25)


def create_line_chart(
    data: pd.DataFrame,
    columns: list[tuple[str, str]],
    title: str,
    y_label: str,
    zero_line: bool = False,
) -> plt.Figure:
    fig, axis = plt.subplots(figsize=(11, 4.5))
    for column, label in columns:
        axis.plot(data["Date"], data[column], label=label, linewidth=1.4)
    if zero_line:
        axis.axhline(0, color="black", linewidth=0.8, linestyle="--", label="0%")
    axis.set_title(title)
    axis.set_xlabel("Date")
    axis.set_ylabel(y_label)
    if len(columns) > 1 or zero_line:
        axis.legend()
    format_date_axis(axis)
    fig.tight_layout()
    return fig


def render_dashboard() -> None:
    st.set_page_config(page_title="Bitcoin 시계열 대시보드", layout="wide")
    st.title("Bitcoin(BTC-USD) 시계열 분석 대시보드")
    st.caption(
        "기존 CSV를 이용한 학습용 탐색 대시보드입니다. "
        "표시 결과는 투자 조언이나 미래 가격 예측이 아닙니다."
    )

    try:
        full_data = load_and_prepare_data()
    except (FileNotFoundError, ValueError, pd.errors.ParserError) as error:
        st.error(f"데이터를 불러오지 못했습니다: {error}")
        return

    min_date = full_data["Date"].min().date()
    max_date = full_data["Date"].max().date()
    start_col, end_col = st.columns(2)
    with start_col:
        start_date = st.date_input(
            "시작일", value=min_date, min_value=min_date, max_value=max_date
        )
    with end_col:
        end_date = st.date_input(
            "종료일", value=max_date, min_value=min_date, max_value=max_date
        )

    try:
        selected = filter_by_date(full_data, start_date, end_date)
    except ValueError as error:
        st.error(str(error))
        return

    if selected.empty:
        st.warning("선택한 기간에 표시할 데이터가 없습니다.")
        return

    summary = calculate_summary(selected)
    st.subheader("선택 기간 요약")
    first_row = st.columns(4)
    first_row[0].metric("시작 Close", format_metric(summary["start_close"], " USD"))
    first_row[1].metric("종료 Close", format_metric(summary["end_close"], " USD"))
    first_row[2].metric("가격 변화율", format_metric(summary["change_pct"], "%"))
    first_row[3].metric("최고 일별 수익률", format_metric(summary["max_return"], "%"))
    second_row = st.columns(3)
    second_row[0].metric("최저 일별 수익률", format_metric(summary["min_return"], "%"))
    second_row[1].metric("평균 일별 수익률", format_metric(summary["mean_return"], "%"))
    second_row[2].metric(
        "평균 30일 변동성", format_metric(summary["mean_volatility"], "%")
    )

    st.subheader("가격 추세")
    price_figure = create_line_chart(
        selected, [("Close", "Close")], "Bitcoin Close", "Price (USD)"
    )
    st.pyplot(price_figure)
    plt.close(price_figure)
    st.caption("선택 기간의 종가 흐름을 선형 축으로 표시합니다.")

    st.subheader("20일·60일 이동평균")
    ma_figure = create_line_chart(
        selected,
        [("Close", "Close"), ("MA20", "MA20"), ("MA60", "MA60")],
        "Bitcoin Close and Moving Averages",
        "Price (USD)",
    )
    st.pyplot(ma_figure)
    plt.close(ma_figure)
    if selected[["MA20", "MA60"]].notna().any().any():
        st.caption("Close와 전체 데이터에서 계산한 MA20·MA60을 비교합니다.")
    else:
        st.info("선택 구간에는 계산 가능한 이동평균 값이 아직 없습니다.")

    st.subheader("일별 수익률")
    if selected["Daily_Return"].notna().any():
        return_figure = create_line_chart(
            selected,
            [("Daily_Return", "Daily Return")],
            "Bitcoin Daily Return",
            "Daily Return (%)",
            zero_line=True,
        )
        st.pyplot(return_figure)
        plt.close(return_figure)
        st.caption("전일 대비 종가 변화율과 0% 기준선을 표시합니다.")
    else:
        st.info("선택 구간에는 계산 가능한 일별 수익률이 없습니다.")

    st.subheader("30일 변동성")
    if selected["Volatility_30"].notna().any():
        volatility_figure = create_line_chart(
            selected,
            [("Volatility_30", "30-day Volatility")],
            "Bitcoin 30-day Volatility",
            "Volatility (%)",
        )
        st.pyplot(volatility_figure)
        plt.close(volatility_figure)
        st.caption("최근 30개 일별 수익률의 표준편차이며 연율화하지 않았습니다.")
    else:
        st.info("선택 구간에는 계산 가능한 30일 변동성 값이 없습니다.")


if __name__ == "__main__":
    render_dashboard()
