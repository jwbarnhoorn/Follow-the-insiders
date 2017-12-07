from bs4 import BeautifulSoup   
import requests
import sqlite3
import datetime
import locale

# encoding=utf8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

#Set local time to NL to parse date correctly.
locale.setlocale(locale.LC_ALL,'nl_NL.UTF-8') #nl_NL.UTF-8 in linux. find correct localWin value at: https://docs.moodle.org/dev/Table_of_locales

#Open DB connection
conn = sqlite3.connect('/home/ec2-user/data/insider_transactions.db', timeout=10)
c = conn.cursor()

#define some attributes
url = "https://www.afm.nl/nl-nl/professionals/registers/meldingenregisters/bestuurders-commissarissen"
Links_of_today = list() 
New_links = list()
Base_url ="https://afm.nl" 
headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}
      
#Check whether there are new links today: 
#1 load old links
c.execute("SELECT * FROM Old_links")
Old_links = [item[0] for item in c.fetchall()] 
print("No. of old links: "+str(len(Old_links)))
#2 get links of today
r=requests.get(url, headers=headers)
soup = BeautifulSoup(r.text, "html.parser")
Found_tags = soup.find('div', class_='results-overview-register registerColCount3').find_all('a')

for tag in Found_tags:
    tag = tag.get('href')
    if "id=" in tag:
        Found_link = Base_url + tag
        Links_of_today.append(Found_link)   
# Remove duplicates out of the list.     
Links_of_today = list(set(Links_of_today))                 
#3 get all the new links                 
for link in Links_of_today:
    if link not in Old_links:
       New_links.append(link)    
print("No. of new links: "+str(len(New_links)))


#For all new links: spider the url and check if update is required
insider_transactions = 0
for link in New_links:  
    r=requests.get(link, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    #Fetch general information
    General_info = soup.find('section', class_='centergrid registerDetail').find_all('span')
    Datum_meldingsplicht = str(General_info[1].getText())
    Datum_meldingsplicht = datetime.datetime.strptime(Datum_meldingsplicht,"%d %b %Y").date()
    Meldingsplichtige = str(General_info[3].getText())

    #Fetch data from table   
    soup = BeautifulSoup(r.text, "html.parser")
    spantags = soup.find_all('span')
    for tag in spantags:
        tag.extract()
    info = soup.find('h2', text='Wijzigingen').findNext('tbody').find_all('td')
    rows = int(len(info)/7)
    j=0
    
    for i in range(0,rows):
        Soort_effect = info[0+j].getText()
        Soort_effect = Soort_effect.strip()
        Uitgevende_instelling = info[1+j].getText()
        Uitgevende_instelling = Uitgevende_instelling.strip()
        Aantal_effecten = info[2+j].getText()
        Aantal_effecten = Aantal_effecten.strip()
        Aantal_effecten = float(Aantal_effecten.replace('.','').replace(',','.'))
        Aantal_effecten = int(Aantal_effecten)
        Valuta = info[3+j].getText()
        Valuta = Valuta.strip()
        Waarde_per_aandeel = info[4+j].getText()
        Waarde_per_aandeel = Waarde_per_aandeel.strip()
        Waarde_per_aandeel = float(Waarde_per_aandeel.replace('.','').replace(',','.'))
        Vrije_hand_beheer = info[6+j].getText()
        Vrije_hand_beheer = Vrije_hand_beheer.strip()
        Totale_waarde = Aantal_effecten * Waarde_per_aandeel
        j += 7 
    #Check whether insider transaction conditions are met and if so store in database
        if Totale_waarde > 10000:
            if "Nee" in Vrije_hand_beheer:
                if ("aandeel" or "stock" or "Aandeel" or "Stock") in Soort_effect:
                    # INSERT the new record into the database.
                    T6 = Datum_meldingsplicht + timedelta(weeks=26)
                    c.execute("INSERT INTO relevant_transactions (Filing_date, Insider_name, Issuer, Security_type, Price_security, Security_amount, Total_value, Currency, Country, T6) VALUES(?,?,?,?,?,?,?,?,?,?)",(Datum_meldingsplicht,Meldingsplichtige,Uitgevende_instelling,Soort_effect,Waarde_per_aandeel,Aantal_effecten,Totale_waarde,Valuta,'Netherlands',T6))
                    conn.commit()
                    # Add counter
                    insider_transactions += 1
                
print("No. of new insider transactions found: "+str(insider_transactions))
       
#Write all crawled links to Old_links
for link in New_links:
    c.execute("INSERT INTO Old_links VALUES(?)",(link,))       
            
#Close DB
conn.commit()     
conn.close()
