from pymongo import MongoClient
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
import logging
import os

logger = logging.getLogger(__name__)

class BattleRecord(BaseModel):
    character1: str
    character2: str
    winner: str
    reasoning: str
    timestamp: datetime

class Database:
    def __init__(self):
        logger.info("Initializing MongoDB connection...")
        try:
            mongodb_uri = os.getenv("MONGODB_URI")
            if not mongodb_uri:
                raise ValueError("MONGODB_URI environment variable is required")
            logger.info(f"Using MongoDB URI: {mongodb_uri}")
            self.client = MongoClient(mongodb_uri)
            self.db = self.client["powerscaler"]
            self.battles = self.db["battles"]
            # Test the connection
            self.client.admin.command('ping')
            logger.info("MongoDB connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}", exc_info=True)
            raise

    def save_battle(self, battle: BattleRecord):
        logger.info(f"Saving battle record: {battle.character1} vs {battle.character2}")
        try:
            battle_dict = battle.model_dump()
            self.battles.insert_one(battle_dict)
            logger.info("Battle record saved successfully")
        except Exception as e:
            logger.error(f"Failed to save battle record: {str(e)}", exc_info=True)
            raise

    def get_battle_history(self) -> List[BattleRecord]:
        logger.info("Retrieving battle history...")
        try:
            records = self.battles.find().sort("timestamp", -1)
            battle_list = [BattleRecord(**record) for record in records]
            logger.info(f"Retrieved {len(battle_list)} battle records")
            return battle_list
        except Exception as e:
            logger.error(f"Failed to retrieve battle history: {str(e)}", exc_info=True)
            raise

db = Database() 