from abc import ABC, abstractmethod
from typing import List
import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection

from core.config import MONGO_CONNECTION_STRING, DB_NAME, DEBTORS_COLLECTION, ENTITIES_COLLECTION
from core.exceptions import RepositoryError
from core.models import DebtorData, EntityData

logger = logging.getLogger(__name__)

class AbstractRepository(ABC):
    @abstractmethod
    async def save_debtors(self, debtors: List[DebtorData]) -> int:
        """
        Save debtor records to the database.
        :param debtors: List of debtor records to save.
        """
        pass

    @abstractmethod
    async def save_entities(self, entities: List[EntityData]) -> int:
        """
        Save entity records to the database.
        :param entities: List of entity records to save.
        """
        pass


class MongoRepository(AbstractRepository):
    _client: AsyncIOMotorClient = None
    _db: AsyncIOMotorDatabase = None

    async def connect(self):
        if not self._client:
            try:
                self._client = AsyncIOMotorClient(MONGO_CONNECTION_STRING)
                self._db = self._client.get_database(DB_NAME)
                logger.info(f"Conectado a MongoDB: {DB_NAME} en {MONGO_CONNECTION_STRING.split('@')[-1]}")
            except Exception as e:
                logger.error(f"No se pudo conectar a MongoDB: {e}")
                raise RepositoryError(f"Error de conexión a MongoDB: {e}")


    async def disconnect(self):
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("Desconectado de MongoDB.")

    def _get_debtors_collection(self) -> AsyncIOMotorCollection:
        if self._db is None:
            raise RepositoryError("La base de datos no está inicializada. Llama a 'connect' primero.")
        return self._db.get_collection(DEBTORS_COLLECTION)


    def _get_entities_collection(self) -> AsyncIOMotorCollection:
        if self._db is None:
            raise RepositoryError("La base de datos no está inicializada. Llama a 'connect' primero.")
        return self._db.get_collection(ENTITIES_COLLECTION)


    async def save_debtors(self, debtors: List[DebtorData]) -> int:
        """
        Save debtor records to the database.
        :param debtors: List of debtor records to save.
        :return: Number of records saved.
        """
        if not debtors:
            logger.info("No hay registros de deudores para guardar.")
            return 0
        try:
            debtors_dicts = [d.model_dump() for d in debtors]
            collection = self._get_debtors_collection()
            result = await collection.insert_many(debtors_dicts)
            count = len(result.inserted_ids)
            logger.info(f"Se insertaron {count} registros de deudores.")
            return count
        except Exception as e:
            logger.error(f"Error al insertar registros de deudores: {e}")
            raise RepositoryError(f"Error al insertar deudores: {e}")

    async def save_entities(self, entities: List[EntityData]) -> int:
        """
        Save entity records to the database.
        :param entities: List of entity records to save.
        :return: Number of records saved.
        """
        if not entities:
            logger.info("No hay registros de entidades para guardar.")
            return 0
        try:
            collection = self._get_entities_collection()
            entities_dicts = [e.model_dump() for e in entities]
            result = await collection.insert_many(entities_dicts)
            count = len(result.inserted_ids)
            logger.info(f"Se insertaron {count} registros de entidades.")
            return count
        except Exception as e:
            logger.error(f"Error al insertar registros de entidades: {e}")
            raise RepositoryError(f"Error al insertar entidades: {e}")
