import requests 
from data_handler import DataHandler

home_currency = 'GBP'
sheety1_url = 'https://api.sheety.co/20e41eb0678ba0bdd23c814c2d17fcfa/travelBudgetTracker/daily'
sheety2_url = 'https://api.sheety.co/20e41eb0678ba0bdd23c814c2d17fcfa/travelBudgetTracker/oneOff'


if __name__ == '__main__':
        
    daily_data = requests.get(sheety1_url).json()
    oneoff_data = requests.get(sheety2_url).json()
    
    datahandler = DataHandler(daily_data, oneoff_data, home_currency)
    datahandler.average_spending()
    datahandler.visualiser()
