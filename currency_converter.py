import requests 
import streamlit as st

API_KEY = st.secrets["EXCHANGE_API_KEY"]

class CurrencyConverter:
    def __init__(self, base_currency, rates):
        self.base_currency = base_currency
        self.rates = rates

    @staticmethod
    def api_request(base_currency):
        url = f'https://v6.exchangerate-api.com/v6/{API_KEY}/latest/{base_currency}'
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if data['result'] != 'success':
                raise ValueError("API returned error.")
            # Just obtain dict of conversion rates of form {'home cur': home cur (1), 'AED': home cur, etc}
            rates = data['conversion_rates']
            return rates

        except requests.RequestException as e:
            raise RuntimeError(f"Currency API request failed: {e}")

    @classmethod
    def from_api(cls, base_currency, desired_currencies):
        # Get exchnage rate data from api 
        rates = cls.api_request(base_currency)
        # Just get desired rates but first check that all are present in exchange rates requested
        # Step 1: Check for missing currencies
        missing = [c for c in desired_currencies if c not in rates]
        if missing:
            raise ValueError(f"Missing currency rates for: {', '.join(missing)}")
        # If none missing then proceed 
        desired_rates = {k: rates[k] for k in desired_currencies}
        return cls(base_currency, desired_rates)  # returns instance
    
    # Uses 'rates' to convert a amount between home and foreign currency
    def convert(self, amount, foreign_currency):
        # Get desired conversion rate 
        conv_rate = next(v for k, v in self.rates.items() if k == foreign_currency)
        try:
            conv_rate = next(v for k, v in self.rates.items() if k == foreign_currency)
        except StopIteration:
            raise ValueError(f'{foreign_currency} not found in the exchange rate data')

        # Calcuate amount in home currency 
        amount_home_cur = round(amount/conv_rate, 2)
        return amount_home_cur

