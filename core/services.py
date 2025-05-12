import logging

from core.data_processor import DataProcessor
from core.exceptions import DataImporterError
from core.file_parser import FileParser
from core.repository import AbstractRepository

logger = logging.getLogger(__name__)


class DataImportService:
    def __init__(self, parser: FileParser, processor: DataProcessor, repository: AbstractRepository):
        self.parser = parser
        self.processor = processor
        self.repository = repository


    async def import_data_from_file(self, file_path: str) -> dict:
        """
        Importa datos desde un archivo y los guarda en la base de datos.
        """
        summary = {"file_path": file_path, "debtors_saved": 0, "entities_saved": 0, "status": "failed"}
        try:
            logger.info(f"Iniciando importación desde el archivo: {file_path}")

            raw_records_stream = self.parser.stream_raw_records(file_path)
            debtors_data, entities_data = await self.processor.aggregate_data(raw_records_stream)

            if not debtors_data and not entities_data:
                logger.info("No se generaron datos procesados para guardar.")
                summary["status"] = "completed_no_data"
                return summary

            debtors_saved_count = await self.repository.save_debtors(debtors_data)
            entities_saved_count = await self.repository.save_entities(entities_data)

            summary["debtors_saved"] = debtors_saved_count
            summary["entities_saved"] = entities_saved_count
            summary["status"] = "completed_successfully"
            logger.info(f"Importación completada exitosamente para {file_path}.")
            return summary
        except DataImporterError as e:
            logger.error(f"Error durante la importación de {file_path}: {e}")
            summary["error_message"] = str(e)
            raise
        except Exception as e:
            logger.critical(f"Error crítico inesperado durante la importación de {file_path}: {e}", exc_info=True)
            summary["error_message"] = "Error crítico inesperado."
            raise DataImporterError(f"Error crítico inesperado: {e}")