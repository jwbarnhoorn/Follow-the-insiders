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
locale.setlocale(locale.LC_ALL,'de_DE.UTF-8') #de_DE.UTF-8 for Linux. find correct localWin value at: https://docs.moodle.org/dev/Table_of_locales

#Open DB connection
conn = sqlite3.connect('/home/ec2-user/data/insider_transactions.db', timeout=10)
c = conn.cursor()

#define some attributes
Urls = list()
Urls.append("https://portal.mvp.bafin.de/database/DealingsInfo/sucheForm.do?d-4000784-p=1&emittentButton=true")
Urls.append("https://portal.mvp.bafin.de/database/DealingsInfo/sucheForm.do?d-4000784-p=2&emittentButton=true")
Urls.append("https://portal.mvp.bafin.de/database/DealingsInfo/sucheForm.do?d-4000784-p=3&emittentButton=true")
Urls.append("https://portal.mvp.bafin.de/database/DealingsInfo/sucheForm.do?d-4000784-p=4&emittentButton=true")
Urls.append("https://portal.mvp.bafin.de/database/DealingsInfo/sucheForm.do?d-4000784-p=5&emittentButton=true")

New_links = list() 
New_entries = list()
Base_url = 'https://portal.mvp.bafin.de/database/DealingsInfo/'
headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}
            
#Get date of yesterday in correct format
today = datetime.now()
yesterday = today - timedelta(days=1)
yesterday = yesterday.strftime('%d.%m.%Y')
yesterday = str(yesterday)

#Check whether there are new entries of yesterday
for url in Urls:
    r=requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    all_entries = soup.find('tbody').find_all('td')
    all_links = soup.find('tbody').find_all('a')

    i = 7
    j = 0
    while i < len(all_entries):    
        if all_entries[i].getText() in yesterday:
            new_entry = Base_url + all_links[j].get('href')
            New_entries.append(new_entry)
        i += 10
        j += 1

print("No. of new entries found: "+str(len(New_entries)))

#Get all the target links from the new entries      
for entry in New_entries:
    r=requests.get(entry, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    link = soup.find('tbody').findNext('a').get('href')
    New_links.append(Base_url+ link)       

print("No. of new links found: "+str(len(New_links)))
#Parse the new links and write to DB if appropriate.         
for link in New_links:
    r=requests.get(link, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    Date = today - timedelta(days=1)
    Date = Date.date()
    Vorname = soup.find('td', text="Vorname:").findNext('td').getText()
    Nachname = soup.find('td', text="Nachname:").findNext('td').getText()
    Meldingsplichtige = Vorname + ' ' + Nachname
    Uitgevende_instelling = soup.find('table', id="3").findNext('td').getText()
    Soort_effect = soup.find('table', id="4").findNext('td').findNext('td').getText()
    Soort_effect = Soort_effect.strip()
    
    Waarde_per_aandeel = soup.find('td', text="Preis:").findNext('td').getText()
    Waarde_per_aandeel = ''.join([i for i in Waarde_per_aandeel if i.isnumeric() or i == "," or i == "."])
    Waarde_per_aandeel = float(Waarde_per_aandeel.replace('.','').replace(',','.'))

    Valuta = soup.find('td', text="Preis:").findNext('td').getText()
    Valuta = ''.join([i for i in Valuta if not i.isdigit()])
    Valuta = Valuta.replace('.','').replace(',','')
    Valuta = Valuta.strip()
    
    Totale_waarde = soup.find('td', text="Aggregiertes Volumen:").findNext('td').getText()
    Totale_waarde = ''.join([i for i in Totale_waarde if i.isnumeric() or i == "," or i == "."])
    Totale_waarde = float(Totale_waarde.replace('.','').replace(',','.'))
    
    Transaction = soup.find('table', id="4").findNext('tbody').findNext('th').findNext('td').getText()
    Transaction = Transaction.strip()
    
    if Waarde_per_aandeel == 0 or Totale_waarde == 0:
        Aantal_effecten = 0
    else:
        Aantal_effecten = int(Totale_waarde/Waarde_per_aandeel)    
    
   
    #Check whether insider transaction conditions are met and if so store in database
    if Totale_waarde > 10000 and \
        Transaction == "Kauf" and \
        "Aktie" or "stock" in Soort_effect:
            # INSERT the new record into the database.
            T6 = Date + timedelta(weeks=26)
            c.execute("INSERT INTO relevant_transactions (Filing_date, Insider_name, Issuer, Security_type, Price_security, Security_amount, Total_value, Currency, Country, T6) VALUES(?,?,?,?,?,?,?,?,?)",(Date,Meldingsplichtige,Uitgevende_instelling,Soort_effect,Waarde_per_aandeel,Aantal_effecten,Totale_waarde,Valuta,'Germany',T6))
            conn.commit()
#Close DB
conn.commit()     
conn.close()
