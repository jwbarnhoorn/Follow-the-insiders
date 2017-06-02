# coding=utf-8
from bs4 import BeautifulSoup   
from urllib2 import urlopen
import sqlite3
import datetime
import locale

#Set local time to NL to parse date correctly.
locale.setlocale(locale.LC_ALL,'nl_NL') #find correct localWin value at: https://docs.moodle.org/dev/Table_of_locales

#Open DB connection
conn = sqlite3.connect('insider_transactions.db', timeout=10)
c = conn.cursor()

#define some attributes
url = "http://www.fsma.be/nl/Supervision/fm/ma/trans_bl/InsTrans.aspx"
Base_url ="http://www.fsma.be" 

Links_of_today = list() 
Found_links = list() 
New_links = list()

            
#Check whether there are new links today: 
#(1) load old links, (2) get links of today and (3) compare for new links
#1 load old links
c.execute("SELECT * FROM Old_links_BE")
Old_links = [item[0] for item in c.fetchall()] 
print("No. of old links: "+str(len(Old_links)))

#2 Get links of today
u = urlopen(url)
try:
   html = u.read().decode('utf-8')
finally:
   u.close()
    
soup = BeautifulSoup(html, "html.parser")
Found_tags = soup.find('table', class_='dataOverview').findAll('a')

for tag in Found_tags:
    tag = tag.get('href')
    enriched_link = Base_url + tag
    Links_of_today.append(enriched_link)

# Remove duplicates out of the list.     
Links_of_today = list(set(Links_of_today))      
           
#3 compare for new links                
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

    #Fetch information
    Datum_meldingsplicht = soup.find('span', text='Transactiedatum').findNext('span').getText()
    Datum_meldingsplicht = datetime.datetime.strptime(Datum_meldingsplicht,"%d-%m-%Y")
    Meldingsplichtige = soup.find('span', text='Naam meldplichtige').findNext('span').getText()
    Uitgevende_instelling = soup.find('span', text='Emittent').findNext('span').getText()
    Soort_effect = soup.find('span', text='Soort financieel instrument').findNext('span').getText()
    Waarde_per_aandeel = soup.find('span', text='Prijs').findNext('span').getText()
    Waarde_per_aandeel.strip()
    Waarde_per_aandeel = float(Waarde_per_aandeel.replace(',','.'))
    Aantal_effecten = soup.find('span', text='Aantal financiële instrumenten').findNext('span').getText()
    Aantal_effecten.strip()
    Aantal_effecten = float(Aantal_effecten.replace(',','.'))
    Totale_waarde = Aantal_effecten * Waarde_per_aandeel
    Valuta = soup.find('span', text='Munt').findNext('span').getText()  
    Soort_transactie = soup.find('span', text='Soort transactie').findNext('span').getText()

    #Check whether insider transaction conditions are met and if so store in database
    if Totale_waarde > 10000 and not "Verkoop" or "Vervreemding" in Soort_transactie and "aandeel" or "stock" in Soort_effect:
               # INSERT the new record into the database.
               c.execute("INSERT INTO relevant_transactions VALUES(?,?,?,?,?,?,?,?,?)",(Datum_meldingsplicht,Meldingsplichtige,Uitgevende_instelling,Soort_effect,Waarde_per_aandeel,Aantal_effecten,Totale_waarde,Valuta,'Belgium'))
               conn.commit()

#Write all crawled links to Old_links
for link in New_links:
    c.execute("INSERT INTO Old_links_BE VALUES(?)",(link,))       
            
#Close DB
conn.commit()     
conn.close()
