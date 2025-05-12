from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from contextlib import asynccontextmanager
import logging
import tempfile
import os
import shutil

from core.config import DB_NAME, MONGO_CONNECTION_STRING
from core.data_processor import DataProcessor
from core.exceptions import FileParsingError, DataImporterError
from core.file_parser import FileParser
from core.repository import MongoRepository, AbstractRepository
from core.services import DataImportService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

mongo_repo_instance = MongoRepository()
file_parser_instance = FileParser()
data_processor_instance = DataProcessor(file_parser=file_parser_instance)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Iniciando API. Conectando a MongoDB: {DB_NAME} en {MONGO_CONNECTION_STRING.split('@')[-1]}")
    await mongo_repo_instance.connect()
    yield
    logger.info("Cerrando API. Desconectando de MongoDB.")
    await mongo_repo_instance.disconnect()


app = FastAPI(
    title="API de Importación de Datos",
    description="API para importar datos de deudores y entidades desde archivos TXT.",
    version="1.0.0",
    lifespan=lifespan
)

def get_repository() -> AbstractRepository:
    return mongo_repo_instance

def get_file_parser() -> FileParser:
    return file_parser_instance

def get_data_processor() -> DataProcessor:
    return data_processor_instance

def get_data_import_service(
    parser: FileParser = Depends(get_file_parser),
    processor: DataProcessor = Depends(get_data_processor),
    repository: AbstractRepository = Depends(get_repository)
) -> DataImportService:
    return DataImportService(parser=parser, processor=processor, repository=repository)


@app.post("/v1/import-txt-file/", summary="Importar datos desde archivo TXT")
async def import_txt_file_endpoint(
        file: UploadFile = File(..., description="Archivo TXT a procesar."),
        service: DataImportService = Depends(get_data_import_service)
):
    """
    Sube un archivo TXT, lo procesa y guarda los datos extraídos en la base de datos.
    """
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="wb") as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            temp_file_path = tmp_file.name
        logger.info(f"Archivo '{file.filename}' subido y guardado temporalmente en '{temp_file_path}'.")

        summary = await service.import_data_from_file(temp_file_path)

        if summary.get("status") == "completed_successfully" or summary.get("status") == "completed_no_data":
            return {
                "filename": file.filename,
                "message": "Archivo procesado.",
                "details": summary
            }
        else:
            logger.error(f"Error durante el procesamiento del archivo '{file.filename}': {summary.get('error_message')}")
            raise HTTPException(
                status_code=500,
                detail=summary.get("error_message", "Error desconocido durante el procesamiento del archivo.")
            )

    except FileParsingError as e:
        logger.error(f"Error de parseo para el archivo '{file.filename}': {e}")
        raise HTTPException(status_code=400, detail=f"Error al parsear el archivo: {e}")
    except DataImporterError as e:
        logger.error(f"Error de importación para el archivo '{file.filename}': {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor al procesar el archivo: {e}")
    except Exception as e:
        logger.critical(f"Error crítico no manejado para el archivo '{file.filename}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno crítico del servidor.")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.info(f"Archivo temporal '{temp_file_path}' eliminado.")
            except Exception as e_rm:
                logger.error(f"No se pudo eliminar el archivo temporal '{temp_file_path}': {e_rm}")
        if file:
            await file.close()