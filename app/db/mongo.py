from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class Database:
    client: AsyncIOMotorClient = None
    
    def connect(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        print("Connected to MongoDB")
        
    def close(self):
        self.client.close()
        print("Closed MongoDB connection")

    def get_db(self):
        return self.client[settings.MONGO_DB]

db = Database()
