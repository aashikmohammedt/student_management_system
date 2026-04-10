import os
from pymongo import MongoClient
from pymongo.errors import ConfigurationError

MONGO_URI = os.environ.get("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is not set.")

try:
    client = MongoClient(MONGO_URI)
    db = client["student_db"]

    students_collection = db["students"]
    users_collection = db["users"]

except ConfigurationError as e:
    raise ValueError(f"Invalid MongoDB configuration: {e}")