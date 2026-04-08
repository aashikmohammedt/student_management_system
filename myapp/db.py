from pymongo import MongoClient

client = MongoClient("mongodb+srv://aashikmohammedt2004_db_user:thamar786@cluster0.czt5pqb.mongodb.net/")
db = client["student_db"]
collection = db["students"] 