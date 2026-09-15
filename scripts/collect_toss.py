from pathlib import Path

import pandas as pd

from market_spectrum_lab.data.toss_client import TossClient


SYMBOLS = [
    "TSLA",
    "AAPL",
    "NVDA",
    "WMT",
    "META",
    "GOOGL",
    "MU",
]

START_DATE = "2020-01-01"


def collect_symbol(
    client: TossClient,
    symbol: str,
) -> None:
    output_path = Path(
        f"data/raw/market/{symbol.lower()}.csv"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    start_timestamp = pd.Timestamp(
        START_DATE,
        tz="UTC",
    )

    old_df: pd.DataFrame | None = None
    last_timestamp = None

    # 기존 CSV가 있으면 마지막 저장 시점을 확인
    if output_path.exists():
        old_df = pd.read_csv(output_path)

        if not old_df.empty:
            last_timestamp = pd.to_datetime(
                old_df["timestamp"],
                utc=True,
            ).max()

    collected_candles: list[dict] = []

    before: str | None = None

    while True:
        page = client.get_daily_candles(
            symbol=symbol,
            count=200,
            before=before,
        )

        candles = page["candles"]

        if not candles:
            break

        page_df = pd.DataFrame(candles)

        page_timestamps = pd.to_datetime(
            page_df["timestamp"],
            utc=True,
        )

        # ---------------------------
        # 기존 CSV가 있는 경우
        # ---------------------------
        if last_timestamp is not None:
            new_mask = (
                page_timestamps > last_timestamp
            )

            collected_candles.extend(
                page_df.loc[
                    new_mask
                ].to_dict("records")
            )

            # 기존 데이터 영역까지 도달하면
            # 더 과거 페이지를 요청할 필요 없음
            if (
                page_timestamps <= last_timestamp
            ).any():
                break

        # ---------------------------
        # 최초 수집인 경우
        # ---------------------------
        else:
            valid_mask = (
                page_timestamps >= start_timestamp
            )

            collected_candles.extend(
                page_df.loc[
                    valid_mask
                ].to_dict("records")
            )

            # START_DATE보다 과거 데이터가
            # 등장하면 pagination 종료
            if (
                page_timestamps < start_timestamp
            ).any():
                break

        # 다음 페이지 존재 여부 확인
        before = page.get("nextBefore")

        if before is None:
            break

    new_df = pd.DataFrame(
        collected_candles
    )

    # ---------------------------
    # 기존 CSV + 신규 데이터
    # ---------------------------
    if old_df is not None:
        if new_df.empty:
            print(
                f"{symbol}: already up to date"
            )
            return

        df = pd.concat(
            [old_df, new_df],
            ignore_index=True,
        )

    # ---------------------------
    # 최초 CSV 생성
    # ---------------------------
    else:
        if new_df.empty:
            print(
                f"{symbol}: no data returned"
            )
            return

        df = new_df

    # pagination 경계 등에서 발생할 수 있는
    # timestamp 중복 제거
    df = df.drop_duplicates(
        subset=["timestamp"],
        keep="last",
    )

    # 시간순으로 정렬
    df = df.sort_values(
        "timestamp"
    )

    # Raw 데이터 저장
    df.to_csv(
        output_path,
        index=False,
    )

    print(
        f"{symbol}: "
        f"added {len(new_df)} new rows, "
        f"{len(df)} total rows"
    )


def main() -> None:
    client = TossClient()

    for symbol in SYMBOLS:
        collect_symbol(
            client=client,
            symbol=symbol,
        )


if __name__ == "__main__":
    main()