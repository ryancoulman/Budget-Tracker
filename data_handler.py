from datetime import date, timedelta
import json
from currency_converter import CurrencyConverter

import streamlit as st
import pandas as pd
import plotly.express as px


class DataHandler:
    def __init__(self, sheet1_data, sheet2_data, home_currency):
        self.home_currency = home_currency

        # Extract actual data from the sheets (remove sheet name wrapper)
        self.sheet1_data = self.extract_sheet_data(sheet1_data)
        self.sheet2_data = self.extract_sheet_data(sheet2_data)

        # Load Json data about countries (e.g., currency codes)
        self.countries_data = self.load_countries_data()

        # Identify unique countries visited from sheet1
        self.visited_countries = self.get_unique_countries(self.sheet1_data)
        # Get the currency codes of those countries
        visited_currencies = self.lookup_country_data('currencyCode', self.visited_countries)
        # Fetch exchange rates only for needed currencies
        self.exchange_rates = CurrencyConverter.from_api(home_currency, visited_currencies)

    # Extract actual data from the sheets (remove sheet name wrapper)
    @staticmethod
    def extract_sheet_data(sheet_data):
        return list(sheet_data.values())[0]

    # Load country metadata from Json file
    @staticmethod
    def load_countries_data():
        with open('countries.json', 'r') as f:
            data = json.load(f)
        return data
    
    # Find all countries visited 
    @staticmethod
    def get_unique_countries(sheet):
        unique_countries = []
        for r in sheet:
            country = r['country'].strip()
            if country not in unique_countries:
                unique_countries.append(country)
        return unique_countries
    
    # Find a given piece of data in countries data correpsonding to given country or countries
    def lookup_country_data(self, param_to_find, countries):

        def find_country(country):
            country = country.strip()
            try:
                value_found = next(d[param_to_find] for d in self.countries_data if d['countryCode'] == country)
                return value_found
            except StopIteration:
                raise ValueError(f"Country code {country} not found in countries_data")
        
        # if countries is list then iterate through
        if isinstance(countries, list):
            return [find_country(c) for c in countries]
        else:
            return find_country(countries)
    
    # Returns most recent spending 
    def recent_spending(self):
        # Check for entry today -> Get date of last entry 
        last_entry = self.sheet1_data[-1]
        country = last_entry['country']
        # Get the currency corresponding to the country 
        currency = self.lookup_country_data('currencyCode', country)
        # Get date of last entry  
        last_date = last_entry['date']
        amount = float(last_entry['total'])
        converted = self.exchange_rates.convert(amount, currency)
        # Store base string to output
        base_str = f'you spent {amount} {currency} ({self.home_currency} {converted})'
        # Check it matches todays date
        if last_date == str(date.today()):
            return 'Today ' + base_str
        # Check if user instead made entry yesterday 
        elif last_date == str(date.today() - timedelta(days=1)):
            return 'Yesterday ' + base_str 
        else:
            return None
        
    def average_spending(self):

        # Used to calcuate the total spend in each country and frequency of each country 
        def calculate_totals(sheet):
            # Calculate total spend and entry counts per country
            totals = {}
            counts = {}
            for row in sheet:
                country = row['country'].strip()
                # Create dict of form {'CountryCode': Total}
                totals[country] = totals.get(country, 0) + row['total']
                counts[country] = counts.get(country, 0) + 1
            return totals, counts
        
        # Calcuates average spend in each country 
        def calculate_avg_spend(total_daily_spend, num_country):
            averages = []
            # Loop through all countries 
            for country in total_daily_spend: 
                daily_total_country = total_daily_spend[country]
                num_country_entries = num_country[country]
                # Find average in local currecny 
                average_loccur = daily_total_country / num_country_entries
                # Get avegerage in home currency 
                currency = self.lookup_country_data('currencyCode', country)
                average_homecur = self.exchange_rates.convert(average_loccur, currency)
                # Get full name of country 
                country_name = self.lookup_country_data('countryCode', country)
                # Store data in a dictionary 
                averages.append({
                    'country': country_name,
                    'currency': currency,
                    'average (local)': average_loccur,
                    'average (home)': average_homecur
                })
            return averages

        # Used to calcuate total oneoff spend in home currency 
        def find_total_home_cur(total):
            return sum(
                self.exchange_rates.convert(amount, self.lookup_country_data('currencyCode', country))
                for country, amount in total.items()
            )
        
        # Get total daily spend for each currency and frequency of occurences 
        total_daily, num_country = calculate_totals(self.sheet1_data) 
        # Get total one off spend for each currency 
        total_oneoff, _ = calculate_totals(self.sheet2_data)
        # Convert to home currency and sum
        total_oneoff_homecur = find_total_home_cur(total_oneoff)

        # Get number of entries overall to determine average
        num_entries_s1 = self.sheet1_data[-1]['id'] - 1

        # Determine most recent country and find total spend there
        last_country = self.sheet1_data[-1]['country']
        self.last_country_fullname = self.lookup_country_data('countryName', last_country)

        # Get average daily spend for each country
        self.daily_averages = calculate_avg_spend(total_daily, num_country)

        # Calcuate daily average in last country, overall, and total average
        self.daily_avg_lastcountry = next(dict for dict in self.daily_averages if dict['country'] == last_country)
        self.daily_average = sum([dict['average (home)'] for dict in self.daily_averages]) / len(self.visited_countries)
        self.total_average = (self.daily_average) + (total_oneoff_homecur / num_entries_s1)

        # Output summary
        # print(daily_averages)
        # print(f"Your daily spending average in {last_country_fullname} is {daily_avg_lastcountry['currency']} {daily_avg_lastcountry['average (local)']} ({self.home_currency} {daily_avg_lastcountry['average (home)']})")
        # print(f"Your overall daily average (excluding one off purchases) is {self.home_currency} {round(daily_average, 2)}")
        # print(f'Your overall average is {self.home_currency} {round(total_average, 2)}')

    # Use streamlit to visually present data 
    def visualiser(self):

        df = pd.DataFrame(self.daily_averages)  

        st.title('Travel Budget Tracker')
        st.write("## Average Spending by Country")
        st.write('')
        st.dataframe(df)
        st.write('')
        st.write('## Spending Stats Overview')
        recent_spending = self.recent_spending()
        # Check if user has made entry today or yesterday 
        if recent_spending is not None:
            st.write(recent_spending)
        st.write(f"Your daily spending average in {self.last_country_fullname} is {self.daily_avg_lastcountry['currency']} {self.daily_avg_lastcountry['average (local)']} ({self.home_currency} {self.daily_avg_lastcountry['average (home)']})")
        st.write(f"Your overall daily average (excluding one off purchases) is {self.home_currency} {round(self.daily_average, 2)}")
        st.write(f'Your overall average is {self.home_currency} {round(self.total_average, 2)}')
        st.write('## Visual Overview')
        fig = px.bar(df, x="country", y="average (home)", color="currency")
        st.plotly_chart(fig)


