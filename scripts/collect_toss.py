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


def main() -> None:
    client = TossClient()

    for symbol in SYMBOLS:
        candles = client.get_daily_candles(
            symbol=symbol,
            count=200,
        )

        new_df = pd.DataFrame(candles)

        if new_df.empty:
            print(f"No candle data returned for {symbol}.")
            continue

        output_path = Path(
            f"data/raw/market/{symbol.lower()}.csv"
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if output_path.exists():
            old_df = pd.read_csv(output_path)

            df = pd.concat(
                [old_df, new_df],
                ignore_index=True,
            )
        else:
            df = new_df

        df = df.drop_duplicates(
            subset=["timestamp"],
            keep="last",
        )

        df = df.sort_values("timestamp")

        df.to_csv(
            output_path,
            index=False,
        )

        print(
            f"{symbol}: saved {len(df)} total rows "
            f"to {output_path}"
        )


if __name__ == "__main__":
    main()