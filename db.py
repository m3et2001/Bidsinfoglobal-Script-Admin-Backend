from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "test")

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

def get_database():
    return db
