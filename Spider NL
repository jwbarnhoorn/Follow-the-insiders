from bs4 import BeautifulSoup   
from urllib.request import urlopen
import sqlite3
import datetime
import locale

#Set local time to NL to parse date correctly.
locale.setlocale(locale.LC_ALL,'nl_NL') #find correct localWin value at: https://docs.moodle.org/dev/Table_of_locales

#Open DB connection
conn = sqlite3.connect('insider_transactions.db', timeout=10)
c = conn.cursor()

#define some attributes
url = "https://www.afm.nl/nl-nl/professionals/registers/meldingenregisters/bestuurders-commissarissen"
Links_of_today = list() 
New_links = list()
Base_url ="https://afm.nl" 
            
#Check whether there are new links today: 
#1 load old links
c.execute("SELECT * FROM Old_links")
Old_links = [item[0] for item in c.fetchall()] 
print("No. of old links: "+str(len(Old_links)))
#2 get links of today
u = urlopen(url)
try:
   html = u.read().decode('utf-8')
finally:
   u.close()
  
soup = BeautifulSoup(html, "html.parser")
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
for link in New_links:  
    u = urlopen(link)
    try:
        html = u.read().decode('utf-8')
    finally:
        u.close()

    soup = BeautifulSoup(html, "html.parser")

    #Fetch general information
    General_info = soup.find('section', class_='centergrid registerDetail').find_all('span')
    Datum_meldingsplicht = str(General_info[1].getText())
    Datum_meldingsplicht = datetime.datetime.strptime(Datum_meldingsplicht,"%d %b %Y")
    Meldingsplichtige = str(General_info[2].getText())

    #Fetch data from table   
    Table = soup.find('h2', text='Wijzigingen').find_all('tr')
    for i in range(0,len(Table)):
        Soort_effect = str(Table[i].findNext('td').getText())
        Uitgevende_instelling = str(Table[i].findNext('td').nextSibling.getText())
        Aantal_effecten = Table[i].findNext('td').nextSibling.nextSibling.getText()
        Aantal_effecten.strip()
        Aantal_effecten = float(Aantal_effecten.replace('.','').replace(',','.'))
        Valuta = str(Table[i].findNext('td').nextSibling.nextSibling.nextSibling.getText())
        Waarde_per_aandeel = Table[i].findNext('td').nextSibling.nextSibling.nextSibling.nextSibling.getText()
        Waarde_per_aandeel.strip()
        Waarde_per_aandeel = float(Waarde_per_aandeel.replace(',','.'))
        Vrije_hand_beheer = str(Table[i].findNext('td').nextSibling.nextSibling.nextSibling.nextSibling.nextSibling.nextSibling.getText())
        Totale_waarde = Aantal_effecten * Waarde_per_aandeel
        
    #Check whether insider transaction conditions are met and if so store in database
        if Totale_waarde > 10000 and \
           Vrije_hand_beheer == "Nee" and \
           "aandeel" or "stock" in Soort_effect:
               # INSERT the new record into the database.
               c.execute("INSERT INTO relevant_transactions VALUES(?,?,?,?,?,?,?,?,?)",(Datum_meldingsplicht,Meldingsplichtige,Uitgevende_instelling,Soort_effect,Waarde_per_aandeel,Aantal_effecten,Totale_waarde,Valuta,'Netherlands'))
               conn.commit()

#Write all crawled links to Old_links
for link in New_links:
    c.execute("INSERT INTO Old_links VALUES(?)",(link,))       
            
#Close DB
conn.commit()     
conn.close()
