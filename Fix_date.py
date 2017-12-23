import sqlite3
import datetime

#Open DB connection
conn = sqlite3.connect("/home/ec2-user/data/insider_transactions.db",timeout=10)
c = conn.cursor()

#Get dates
To_Fix = list()
c.execute("SELECT DISTINCT Filing_date FROM relevant_transactions")
Dates = [item[0] for item in c.fetchall()]
for Date in Dates:
    if "/" in Date:
        print(Date)
        Fix = datetime.datetime.strptime(Date, '%d/%m/%Y')
        Fix = datetime.datetime.strftime(Fix, '%Y-%m-%d')
        print(Fix)
        c.execute("UPDATE relevant_transactions SET Filing_date = ? WHERE Filing_date = ?",(Fix, Date))
        conn.commit() 
       
#Close DB    
conn.close()