import requests
from data_handler import DataHandler
import streamlit as st

home_currency = 'GBP'

BASE_URL = "https://api.sheetson.com/v2/sheets"
SPREADSHEET_ID = "1N4MtOBIp0WL7z4GZPUYCHflm4B2glJLJCoeRuqf7JvA"
API_KEY = st.secrets["SHEETSON_API_KEY"]
HEADERS = {
    "X-Spreadsheet-Id": SPREADSHEET_ID,
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

if __name__ == '__main__':

    # Check request response 
    response = requests.get(f"{BASE_URL}/Daily", headers=HEADERS)
    print("Status:", response.status_code)

    # Fetch sheet data (Fetch 100 rows)
    daily_response = requests.get(f"{BASE_URL}/Daily?limit={100}", headers=HEADERS).json()
    oneoff_response = requests.get(f"{BASE_URL}/OneOff", headers=HEADERS).json()

    # Extract the "results" arrays for Table data
    daily_data = daily_response.get("results", [])
    oneoff_data = oneoff_response.get("results", [])

    # Process the data
    datahandler = DataHandler(daily_data, oneoff_data, home_currency)
    datahandler.average_spending()
    datahandler.visualiser()
