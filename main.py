import argparse
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta

class ApiRequester:
    API_URL = "https://api.privatbank.ua/p24api/exchange_rates?json&date={}"

    async def fetch_data(self, date):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.API_URL.format(date)) as response:
                return await response.json()

class CurrencyParser:
    @staticmethod
    def parse_exchange_rates(data):
        parsed_data = json.loads(data)
        return parsed_data.get('exchangeRate', [])

class CurrencyFetcher:
    def __init__(self, days):
        self.days = days

    async def fetch_currency_data(self):
        api_requester = ApiRequester()
        currency_data = []

        for i in range(self.days):
            date = (datetime.now() - timedelta(days=i)).strftime("%d.%m.%Y")
            data = await api_requester.fetch_data(date)
            parsed_data = CurrencyParser.parse_exchange_rates(data)
            currency_data.append({date: parsed_data})

        return currency_data

def format_output(currency_data):
    formatted_data = []
    for entry in currency_data:
        date, rates = list(entry.items())[0]
        formatted_entry = {date: {}}

        for rate in rates:
            currency = rate['currency']
            formatted_entry[date][currency] = {
                'sale': rate['saleRate'],
                'purchase': rate['purchaseRate']
            }

        formatted_data.append(formatted_entry)

    return formatted_data

async def main():
    parser = argparse.ArgumentParser(description="Fetch EUR and USD exchange rates from PrivatBank for the last few days.")
    parser.add_argument("days", type=int, help="Number of days to retrieve exchange rates for")
    args = parser.parse_args()

    currency_fetcher = CurrencyFetcher(args.days)
    currency_data = await currency_fetcher.fetch_currency_data()
    formatted_data = format_output(currency_data)
    print(json.dumps(formatted_data, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
