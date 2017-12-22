from bs4 import BeautifulSoup   
import requests
import sqlite3
from datetime import datetime, timedelta
import locale

# encoding=utf8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

#Set local time to NL to parse date correctly.
locale.setlocale(locale.LC_ALL,'nl_NL.UTF-8') #nl_NL.UTF-8 for Linux / Dutch_Netherlands.1252 for Windows

#Open DB connection
conn = sqlite3.connect('/home/ec2-user/data/insider_transactions.db', timeout=10)
c = conn.cursor()

#define some attributes
url = "https://www.fsma.be/nl/transaction-search"
Base_url = "https://www.fsma.be"
New_links = list()
headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}

#Get date of yesterday in correct format
today = datetime.now().date()
yesterday = today - timedelta(days=1)
Date = yesterday.strftime('%Y-%m-%d')
yesterday_dt = yesterday.strftime('%d/%m/%Y')
yesterday = str(yesterday_dt)
            
#Get new links of today
r=requests.get(url, headers=headers)
soup = BeautifulSoup(r.text, "html.parser")

All_links = soup.find('tbody').find_all('a')
All_dates = soup.find('tbody').find_all('span', class_ = 'date-display-single')

i = 0
for i in range(0,len(All_dates)):
    if All_dates[i].getText() in yesterday:
        link = Base_url + All_links[i].get('href')
        New_links.append(link)

print("No. of new links found: "+str(len(New_links)))

#For all new links: spider the url and check if new insider transaction is found
insider_transactions = 0
for link in New_links:  
    r=requests.get(link, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    soup = soup.find('div', class_ = 'ds-1col node node-manager-transactions node-view-full node-manager-transactions-full view-mode-full clearfix') 
    #Fetch information  
    Meldingsplichtige = soup.find(text='Naam meldplichtige').findNext('div').getText()
    Uitgevende_instelling = soup.find(text='Emittent').findNext('div').getText()
    Soort_effect = soup.find(text='Soort financieel instrument').findNext('div').getText()
    Waarde_per_aandeel = soup.find(text='Prijs').findNext('div').getText()
    Waarde_per_aandeel = Waarde_per_aandeel.strip()
    Waarde_per_aandeel = float(Waarde_per_aandeel.replace('.','').replace(',','.'))
    Aantal_effecten = soup.find(text='Prijs').findNext('div').getText()
    Aantal_effecten = Aantal_effecten.strip()   
    Aantal_effecten = float(Aantal_effecten.replace('.','').replace(',','.'))
    Totale_waarde = soup.find(text='Totaal bedrag').findNext('div').getText()
    Totale_waarde = Totale_waarde.strip()
    Totale_waarde = float(Totale_waarde.replace('.','').replace(',','.'))
    Valuta = soup.find(text='Munt').findNext('div').getText() 
    Soort_transactie = soup.find(text='Soort transactie').findNext('div').getText()

    #Check whether insider transaction conditions are met and if so store in database
    if Totale_waarde > 10000:
        if ("Aankoop" or "Verwerving") in Soort_transactie:
            if ("Aandeel" or "Stock") in Soort_effect:
                # INSERT the new record into the database.
                T6 = today - timedelta(days=1) + timedelta(weeks=26)
                c.execute("INSERT INTO relevant_transactions (Filing_date, Insider_name, Issuer, Security_type, Price_security, Security_amount, Total_value, Currency, Country, T6) VALUES(?,?,?,?,?,?,?,?,?,?)",(Date,Meldingsplichtige,Uitgevende_instelling,Soort_effect,Waarde_per_aandeel,Aantal_effecten,Totale_waarde,Valuta,'Belgium',T6))
                conn.commit()
                # Add counter
                insider_transactions += 1
                
print("No. of new insider transactions found: "+str(insider_transactions))
              
#Close DB
conn.commit()     
conn.close()

