from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGODB_CONNECTION_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DB_NAME", "test")

client = MongoClient("mongodb+srv://bidsinfoglobal:3N4ZRDaS6H64GajL@qa.t5cmca1.mongodb.net")
db = client["script"]

def get_database():
    return db
