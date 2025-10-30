"""This app does foreign exchange requests"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

app = FastAPI(title="Foreign Exchange API")


class CurrencyCheck(BaseModel):
    currency_name: str


class ExchangeRateRequest(BaseModel):
    from_currency: str
    to_currency: str
    amount: float = 1.0


@app.get("/currencies")
async def currencies_supported():
    """Get list of supported currencies"""
    currencies = currency_list()
    return currencies


def currency_list():
    """List of currencies supported"""
    currency_list = {"dollar": "USD", "euro": "EUR", "british sterling": "GBP"}
    return currency_list


@app.post("/currency_supported")
async def currency_supported(input_currency: CurrencyCheck):
    """Tests if the inputted currency is supported"""
    currencies = currency_list()
    if currencies.get(input_currency.currency_name):
        return {"message": "Currency is accepted"}
    else:
        return {"message": "Currency not supported"}


@app.get("/exchange_rate")
async def get_exchange_rate(
    from_currency: str = "USD",
    to_currency: str = "EUR",
    amount: float = 1.0
):
    """Get current exchange rate between two currencies using Frankfurter API"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"https://api.frankfurter.app/latest",
                params={"from": from_currency.upper(), "to": to_currency.upper(), "amount": amount}
            )
            response.raise_for_status()
            data = response.json()
            return {
                "from": from_currency.upper(),
                "to": to_currency.upper(),
                "amount": amount,
                "converted_amount": data["rates"][to_currency.upper()],
                "rate": data["rates"][to_currency.upper()] / amount,
                "date": data["date"]
            }
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=400, detail="Invalid currency code or API error")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching exchange rate: {str(e)}")
