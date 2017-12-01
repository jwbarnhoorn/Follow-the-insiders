import sqlite3
from datetime import datetime, timedelta

#Open DB connection
conn = sqlite3.connect('/home/ec2-user/data/insider_transactions.db', timeout=10)
conn.row_factory = sqlite3.Row
c = conn.cursor()

#Remove time from all datetime elements
c.execute("SELECT DISTINCT Filing_date FROM relevant_transactions")
Dates = [item[0] for item in c.fetchall()] 

for i in range(0,len(Dates)):
        Corrected_date = datetime.strptime(Dates[i][:11], '%Y-%m-%d').date()
        c.execute("UPDATE relevant_transactions SET Filing_date = ? WHERE Filing_date = ?",(Corrected_date,Dates[i],))
        conn.commit()

#Fix SpiderBE error
c.execute("SELECT DISTINCT Filing_date FROM relevant_transactions WHERE Country = ?",('Belgium',))
Dates = [item[0] for item in c.fetchall()] 
print("Number of Fixes to work on: "+str(len(Dates)))

for Date in Dates:
        Date = datetime.strptime(Date, '%Y-%m-%d')
        Date = Date.date()
        print(Date)
        Fix = Date - timedelta(days=1)
        print(Fix)
        c.execute("UPDATE relevant_transactions SET Filing_date = ? WHERE Country = ? AND Filing_date = ?",(Fix,'Belgium',Date,))
        conn.commit() 

#Set T6 fields
c.execute("SELECT DISTINCT Filing_date FROM relevant_transactions")
Dates2 = [item[0] for item in c.fetchall()]  
print("Number of Dates to work on: "+str(len(Dates2)))

for Date2 in Dates2:
        Date2 = datetime.strptime(Date2, '%Y-%m-%d')
        Date2 = Date2.date()
        T6 = Date2 + timedelta(weeks=26)
        c.execute("UPDATE relevant_transactions SET T6 = ? WHERE Filing_date = ?",(T6, Date2,))
        conn.commit() 

#Close DB    
conn.close()
