import os
from dotenv import load_dotenv

load_dotenv()

MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")
DB_NAME = os.getenv("DB_NAME")

ENTITY_CODE_SLICE = slice(0, 5)
CUIT_CUIL_SLICE = slice(13, 24)
SITUATION_SLICE = slice(27, 29)
TOTAL_SLICE = slice(30, 41)

DEBTORS_COLLECTION= "debtors"
ENTITIES_COLLECTION = "entities"