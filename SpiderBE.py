# coding=utf-8
from bs4 import BeautifulSoup   
import requests
import sqlite3
from datetime import datetime, timedelta
import locale

#Set local time to NL to parse date correctly.
locale.setlocale(locale.LC_ALL,'Dutch_Netherlands.1252') #nl_NL for Linux.

#Open DB connection
conn = sqlite3.connect('insider_transactions.db', timeout=10)
c = conn.cursor()

#define some attributes
url = "https://www.fsma.be/nl/transaction-search"
Base_url = "https://www.fsma.be"
New_links = list()
headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}

#Get date of yesterday in correct format
today = datetime.now()
yesterday = today - timedelta(days=1)
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
Datum_meldingsplicht = yesterday_dt
for link in New_links:  
    r=requests.get(link, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    info = soup.find('div', class_ = 'ds-1col node node-manager-transactions node-view-full node-manager-transactions-full view-mode-full clearfix').find_all('div', class_ = 'field-item even')
    #Fetch information  
    Meldingsplichtige = info[1].getText()
    Uitgevende_instelling = info[3].getText()
    Soort_effect = info[4].getText()
    Waarde_per_aandeel = info[10].getText()
    Waarde_per_aandeel = Waarde_per_aandeel.strip()
    Waarde_per_aandeel = float(Waarde_per_aandeel.replace('.','').replace(',','.'))
    Aantal_effecten = info[9].getText()
    Aantal_effecten = Aantal_effecten.strip()
    Aantal_effecten = int(Aantal_effecten.replace('.',''))
    Totale_waarde = info[11].getText()
    Totale_waarde = Totale_waarde.strip()
    Totale_waarde = float(Totale_waarde.replace('.','').replace(',','.'))
    Valuta = info[8].getText()  
    Soort_transactie = info[5].getText()

    #Check whether insider transaction conditions are met and if so store in database
    if Totale_waarde > 10000:
        if ("Aankoop" or "Verwerving") in Soort_transactie:
            if ("Aandeel" or "Stock") in Soort_effect:
                # INSERT the new record into the database.
                c.execute("INSERT INTO relevant_transactions VALUES(?,?,?,?,?,?,?,?,?)",(Datum_meldingsplicht,Meldingsplichtige,Uitgevende_instelling,Soort_effect,Waarde_per_aandeel,Aantal_effecten,Totale_waarde,Valuta,'Belgium'))
                conn.commit()
                # Add counter
                insider_transactions += 1
                
print("No. of new insider transactions found: "+str(insider_transactions))
              
#Close DB
conn.commit()     
conn.close()

