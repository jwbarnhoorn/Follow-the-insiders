import web
import json
from datetime import datetime, timedelta
from babel import numbers

urls = (
        "/", "index",
       "/transactions/", "transactions")

render = web.template.render('.')

class index:
    def GET(self):
        return render.index()

class transactions:
    def GET(self):
        db = web.database(dbn='sqlite', db='////home/ec2-user/data/insider_transactions.db')
        #Create dict to prevent SQL injection attack and store time of today minus 30 days.
        LatestDate = datetime.now() - timedelta(days=30)
        vars = {"key":LatestDate}
        #Query DB and get all transactions 
        transactions = db.select('relevant_transactions', where='Filing_date > $key', vars=vars)   
        transactions = [ dict(entry) for entry in transactions ]   
        """
        for item in transactions:
            item['Total_value'] = numbers.format_currency(item['Total_value'],item['Currency'])   
        """
        return json.dumps(transactions)

if __name__ == "__main__": 
    app = web.application(urls, globals(), True)
    app.run() 
