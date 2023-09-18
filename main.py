import argparse
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
import websockets
from aiofile import AIOFile
from aiopath import Path

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

async def handle_chat(websocket, path):
    async for message in websocket:
        if message == "exchange":
            log_exchange_command()
            # Отримати та надіслати поточний курс валют
            currency_data = await fetch_currency_data(1)
            formatted_data = format_output(currency_data)
            await websocket.send(json.dumps(formatted_data, indent=2))
        elif message.startswith("exchange "):
            parts = message.split()
            if len(parts) == 2 and parts[1].isdigit():
                num_days = int(parts[1])
                currency_data = await fetch_currency_data(num_days)
                formatted_data = get_currency_data_for_last_days(currency_data, num_days)
                await websocket.send(json.dumps(formatted_data, indent=2))
            else:
                await websocket.send("Invalid command format for 'exchange'. Use 'exchange <num_days>'.")
        else:
            await websocket.send("Unknown command. Available commands: 'exchange' and 'exchange <num_days>'.")

async def fetch_currency_data(num_days):
    currency_fetcher = CurrencyFetcher(num_days)
    return await currency_fetcher.fetch_currency_data()

def get_currency_data_for_last_days(currency_data, num_days):
    last_days_data = currency_data[:num_days]
    return format_output(last_days_data)

async def log_exchange_command():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"exchange command called at {timestamp}\n"

    async with AIOFile(Path("exchange_logs.txt"), "a") as afp:
        await afp.write(log_message)

async def main():
    parser = argparse.ArgumentParser(description="Fetch EUR and USD exchange rates from PrivatBank for the last few days.")
    parser.add_argument("days", type=int, help="Number of days to retrieve exchange rates for")
    parser.add_argument("--currencies", nargs="+", default=["EUR", "USD"], help="Additional currencies to retrieve")
    args = parser.parse_args()

    start_server = websockets.serve(handle_chat, "localhost", 8765)
    asyncio.create_task(start_server)

    # Print exchange rates for the specified number of days
    currency_data = await fetch_currency_data(args.days)
    formatted_data = get_currency_data_for_last_days(currency_data, args.days)
    print(json.dumps(formatted_data, indent=2))

    await asyncio.sleep(1)  # Ensure the server is started

if __name__ == "__main__":
    asyncio.run(main())
