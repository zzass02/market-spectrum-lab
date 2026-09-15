import os

import requests
from dotenv import load_dotenv


class TossClient:
    BASE_URL = "https://openapi.tossinvest.com"

    def __init__(self) -> None:
        load_dotenv()

        self.client_id = os.getenv("TOSS_CLIENT_ID")
        self.client_secret = os.getenv("TOSS_CLIENT_SECRET")
        self.access_token: str | None = None

        if not self.client_id or not self.client_secret:
            raise RuntimeError(
                "TOSS_CLIENT_ID and TOSS_CLIENT_SECRET must be set in .env"
            )

    def authenticate(self) -> str:
        response = requests.post(
            f"{self.BASE_URL}/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()
        self.access_token = data["access_token"]

        return self.access_token

    def get_daily_candles(
        self,
        symbol: str,
        count: int = 200,
        before: str | None = None,
    ) -> dict:
        if self.access_token is None:
            self.authenticate()

        params = {
            "symbol": symbol,
            "interval": "1d",
            "count": count,
            "adjusted": True,
        }

        if before is not None:
            params["before"] = before

        response = requests.get(
            f"{self.BASE_URL}/api/v1/candles",
            headers={
                "Authorization":
                    f"Bearer {self.access_token}",
            },
            params=params,
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        return data["result"]