from pymongo import MongoClient
import os
from dotenv import dotenv_values

config = dotenv_values(".env")
MONGO_URI = config["MONGODB_CONNECTION_URI"]
DATABASE_NAME = config["DB_NAME"]

client = MongoClient(MONGO_URI)
# client = MongoClient("mongodb+srv://bidsinfoglobal:3N4ZRDaS6H64GajL@qa.t5cmca1.mongodb.net")
db = client[DATABASE_NAME]

def get_database():
    return db
