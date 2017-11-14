import os

Origin = "/home/ec2-user/data/insider_transactions.db"

os.system("aws s3 cp --region eu-central-1" + Origin + "s3://followtheinsiders/")