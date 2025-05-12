import asyncio
import aiofiles
import os
from typing import Any, Dict, List, Tuple

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from dotenv import load_dotenv

load_dotenv()


ENTITY_CODE_SLICE = slice(0, 5)
CUIT_CUIL_SLICE = slice(13, 24)
SITUATION_SLICE = slice(27, 29)
TOTAL_SLICE = slice(30, 41)


def parse_numeric_value(value: str) -> float:
    """
    Convierte un token de cadena (ej: "60,6", ",0", "  7,5") a float.
    Maneja comas como decimales y cadenas vacías/inválidas como 0.0.
    """
    if not value:
        return 0.0
    cleaned_token = value.strip()
    if not cleaned_token or cleaned_token == ",":
        return 0.0
    try:
        return float(cleaned_token.replace(',', '.'))
    except ValueError:
        print(f"Advertencia: No se pudo convertir '{value}' a float. Se usará 0.0.")
        return 0.0


def parse_line(line: str) -> Tuple[None, None, None] | Tuple[str, str, str, str]:
    """
    Parsea una línea del archivo TXT.
    Retorna (codigo_entidad_str, cuit_cuil_str, total_str)
    o (None, None, []) si la línea no es válida.
    """
    codigo_entidad_str = line[ENTITY_CODE_SLICE].strip()
    cuit_cuil_str = line[CUIT_CUIL_SLICE].strip()
    situation_str = line[SITUATION_SLICE].strip()
    total_str = line[TOTAL_SLICE].strip()

    if not codigo_entidad_str.isdigit() or not cuit_cuil_str.isdigit():
        print("Advertencia: Código de entidad o CUIT/CUIL no numérico en ID block . Se omite línea.")
        return None, None, None

    return codigo_entidad_str, cuit_cuil_str, situation_str, total_str

async def process_file(file_path: str) -> Dict[str, Dict]:
    """
    Procesa un archivo de texto y devuelve un diccionario con la información extraída.
    :param file_path:
    :return:
    """

    debtors_records = {}
    entities_records = {}

    try:
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
            lines = await file.readlines()

            for i, line in enumerate(lines):
                entity_code, cuit_cuil, situation, total = parse_line(line)

                if entity_code is None or cuit_cuil is None:
                    continue

                try:
                    entity_code_value = int(entity_code)
                    cuit_cuil_value = int(cuit_cuil)
                except ValueError:
                    print(f"Advertencia: No se pudo convertir '{entity_code}' o '{cuit_cuil}' a int. Se omite línea.")
                    continue

                current_situation = parse_numeric_value(situation)
                current_total = parse_numeric_value(total)

                if cuit_cuil not in debtors_records:
                    debtors_records[cuit_cuil] = {
                        'entity_code': entity_code_value,
                        'cuit_cuil': cuit_cuil_value,
                        'situation': [],
                        'loans': []
                    }

                debtors_records[cuit_cuil]['situation'].append(current_situation)
                debtors_records[cuit_cuil]['loans'].append(current_total)

                if entity_code_value not in entities_records:
                    entities_records[entity_code_value] = {
                        'loans': []
                    }
                entities_records[entity_code_value]['loans'].append(current_total)

        return {'debtors': debtors_records, 'entities': entities_records}

    except FileNotFoundError:
        print(f"Error: El archivo {file_path} no fue encontrado.")
        return {}
    except Exception as e:
        print(f"Error inesperado al procesar el archivo: {e}")
        return {}

def prepare_debtors_records(debtors_records: Dict[str, Dict]) -> List[Dict[str, Any]]:
    """
    Prepara los registros de deudores para su uso posterior.
    :param debtors_records:
    :return:
    """
    records_to_insert: List[Dict[str, Any]] = []

    for cuit_cuil, record in debtors_records.items():
        max_situation = max(record['situation']) if record['situation'] else 0.0
        sum_loans = sum(record['loans']) if record['loans'] else 0.0

        records_to_insert.append({
            'entity_code': record['entity_code'],
            'cuit_cuil': cuit_cuil,
            'situation': max_situation,
            'loans': sum_loans
        })

    return records_to_insert


def prepare_entities_records(entities_records: Dict[str, Dict]) -> List[Dict[str, Any]]:
    """
    Prepara los registros de entidades para su uso posterior.
    :param entities_records:
    :return:
    """
    records_to_insert: List[Dict[str, Any]] = []

    for entity_code, record in entities_records.items():
        sum_loans = sum(record['loans']) if record['loans'] else 0.0

        records_to_insert.append({
            'entity_code': entity_code,
            'loans': sum_loans
        })

    return records_to_insert

def mongodb_client():
    """
    Crea un cliente de MongoDB.
    :return:
    """

    client = AsyncIOMotorClient(os.getenv("MONGO_CONNECTION_STRING"))
    db = client.get_database(os.getenv("DB_NAME"))

    return db

async def insert_records(collection: AsyncIOMotorCollection, records: List[Dict[str, Any]]):
    """
    Inserta registros en la colección de MongoDB.
    :param collection:
    :param records:
    :return:
    """
    if not records:
        print("No hay registros para insertar.")
        return

    try:
        await collection.insert_many(records)
        print(f"Se insertaron {len(records)} registros en la colección.")
    except Exception as e:
        print(f"Error al insertar registros: {e}")

async def insert_debtors_records(records: List[Dict[str, Any]]):
    """
    Inserta registros de deudores en la colección de MongoDB.
    :param records:
    :return:
    """
    db = mongodb_client()
    debtors_collection = db.get_collection('debtors')

    await insert_records(debtors_collection, records)

async def insert_entities_records(records: List[Dict[str, Any]]):
    """
    Inserta registros de entidades en la colección de MongoDB.
    :param records:
    :return:
    """
    db = mongodb_client()
    entities_collection = db.get_collection('entities')

    await insert_records(entities_collection, records)

async def main():
    """
    Función principal para ejecutar el procesamiento de archivos.
    """
    file_path = '/Users/erianrincon/Downloads/Copia de Copia de deudores.txt'  # Cambia esto por la ruta de tu archivo
    records = await process_file(file_path)

    debtors_records = prepare_debtors_records(records.get('debtors', {}))
    entities_records = prepare_entities_records(records.get('entities', {}))

    await insert_debtors_records(debtors_records)
    await insert_entities_records(entities_records)

if __name__ == "__main__":
    asyncio.run(main())
