import aiofiles
import logging

from typing import Optional

from core.config import ENTITY_CODE_SLICE, CUIT_CUIL_SLICE, SITUATION_SLICE, TOTAL_SLICE
from core.exceptions import FileParsingError
from core.models import RawRecord


logger = logging.getLogger(__name__)

class FileParser:
    def _parse_single_line(self, line: str) -> Optional[RawRecord]:
        """
        Parses a single line of the file and extracts the relevant fields.
        :param line: The line to parse.
        :return: A RawRecord object containing the parsed data or None if the line is empty.
        """
        if not line.strip():
            return None

        try:
            codigo_entidad_str = line[ENTITY_CODE_SLICE].strip()
            cuit_cuil_str = line[CUIT_CUIL_SLICE].strip()
            situation_str = line[SITUATION_SLICE].strip()
            total_str = line[TOTAL_SLICE].strip()

            if not codigo_entidad_str.isdigit() or not cuit_cuil_str.isdigit():
                print("Advertencia: Código de entidad o CUIT/CUIL no numérico en ID block . Se omite línea.")
                return None

            return RawRecord(
                entity_code_str=codigo_entidad_str,
                cuit_cuil_str=cuit_cuil_str,
                situation_str=situation_str,
                total_str=total_str
            )
        except IndexError:
            print("Advertencia: Línea no válida. Se omite línea.")
            return None


    async def stream_raw_records(self, file_path: str):
        """
        Streams raw records from a file.
        :param file_path: The path to the file.
        :return: A generator that yields RawRecord objects.
        """
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                async for line in f:
                    record = self._parse_single_line(line)
                    if record:
                        yield record
        except FileNotFoundError:
            logger.error(f"Archivo no encontrado: {file_path}")
            raise FileParsingError(f"Archivo no encontrado: {file_path}")
        except Exception as e:
            logger.error(f"Error inesperado al leer el archivo {file_path}: {e}")
            raise FileParsingError(f"Error inesperado al leer el archivo {file_path}: {e}")

    def parse_numeric_value(self, value: str) -> float:
        """
        Convierte un string a float. Usado por DataProcessor.
        """
        if not value:
            return 0.0
        cleaned_token = value.strip()
        if not cleaned_token or cleaned_token == ",":
            return 0.0
        try:
            return float(cleaned_token.replace(",", "."))
        except ValueError:
            logger.warning(
                f"No se pudo convertir '{value}' a float. Se usará 0.0."
            )
            return 0.0
