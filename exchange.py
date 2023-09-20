import asyncio
from datetime import datetime, timedelta
import logging
import sys

from aiohttp import ClientSession, ClientConnectionError

currencies = ['EUR', 'USD']


class APIRequest:
    def __init__(self, url):
        self.url = url

    async def send_request(self, session: ClientSession, date: datetime) -> dict | None:
        date_str = date.strftime("%d.%m.%Y")
        try:
            async with session.get(self.url + date_str) as response:
                if response.status == 200:
                    return await response.json()
                logging.error(f"Error status {response.status}")
        except ClientConnectionError as e:
            logging.error(f"Connection error: {e}")


class RequestHandler:
    def __init__(self, currencies):
        self.currencies = currencies

    def get_data(self, response_data):
        res = {}
        exchange_rates = response_data["exchangeRate"]
        for i in exchange_rates:
            currency = i["currency"]
            if currency in self.currencies:
                res[currency] = {
                    "sale": i.get("saleRate") or "No data",
                    'purchase': i.get("purchaseRate") or "No data"
                }
        return res

    async def get_exchange_rates(self, days_amount=1):
        tasks = []
        today = datetime.now()
        async with ClientSession() as session:
            api_request = APIRequest(
                "https://api.privatbank.ua/p24api/exchange_rates?json&date=")
            for day in range(days_amount):
                cur_day = today - timedelta(days=day)
                tasks.append(asyncio.create_task(
                    api_request.send_request(session, cur_day)))
            results = await asyncio.gather(*tasks)
            res = {}
            for data in results:
                res[data["date"]] = self.get_data(data)
        return res


async def main():
    if len(sys.argv) < 2:
        raise ValueError("Please enter amount of days")

    try:
        days_amount = int(sys.argv[1])
    except ValueError:
        print("Invalid input. Please try again")

    if days_amount > 10:
        raise ValueError("The number of days should not be more than 10")

    handler = RequestHandler(currencies)
    print(await handler.get_exchange_rates(int(sys.argv[1])))


if __name__ == "__main__":
    currencies.extend(sys.argv[2:])
    asyncio.run(main())
