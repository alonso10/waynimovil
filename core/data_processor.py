from typing import AsyncIterable, List, Dict, Tuple
import logging

from core.exceptions import DataProcessingError
from core.file_parser import FileParser
from core.models import RawRecord, ProcessedRecordData, DebtorData, EntityData

logger = logging.getLogger(__name__)

class DataProcessor:
    """
    Clase para procesar datos de entidades.
    """

    def __init__(self, file_parser: FileParser):
        self.file_parser = file_parser


    def _raw_to_processed_data(self, raw_record: RawRecord) -> ProcessedRecordData | None:
        """
        Convierte un RawRecord a un objeto ProcessedRecordData.
        :param raw_record:
        :return:
        """
        try:
            entity_code_value = int(raw_record.entity_code_str)
            cuit_cuil_value = int(raw_record.cuit_cuil_str)
            situation_value = self.file_parser.parse_numeric_value(raw_record.situation_str)
            total_value = self.file_parser.parse_numeric_value(raw_record.total_str)

            return ProcessedRecordData(
                entity_code=entity_code_value,
                cuit_cuil=cuit_cuil_value,
                situation=situation_value,
                loans=total_value
            )
        except ValueError as e:
            logger.warning(f"Error de conversión de tipos para el registro: {raw_record}, error: {e}. Se omite.")
            return None
        except Exception as e:
            logger.error(f"Error inesperado procesando RawRecord {raw_record}: {e}")
            raise DataProcessingError(f"Error procesando RawRecord: {e}")


    async def aggregate_data(
            self, raw_records: AsyncIterable[RawRecord]
    ) -> Tuple[List[DebtorData], List[EntityData]]:
        """
        Toma RawRecords, los procesa y agrega para generar listas de DebtorData y EntityData.
        """
        debtors_temp_aggregation: Dict[int, Dict] = {}
        entities_temp_aggregation: Dict[int, Dict] = {}

        async for raw_record in raw_records:
            processed_data = self._raw_to_processed_data(raw_record)
            if not processed_data:
                continue

            cuit = processed_data.cuit_cuil
            if cuit not in debtors_temp_aggregation:
                debtors_temp_aggregation[cuit] = {
                    "situations": [],
                    "loans": [],
                    "entity_code": processed_data.entity_code
                }
            debtors_temp_aggregation[cuit]["situations"].append(processed_data.situation)
            debtors_temp_aggregation[cuit]["loans"].append(processed_data.loans)

            entity = processed_data.entity_code
            if entity not in entities_temp_aggregation:
                entities_temp_aggregation[entity] = {"loans": []}
            entities_temp_aggregation[entity]["loans"].append(processed_data.loans)

        final_debtors: List[DebtorData] = []
        for cuit, data in debtors_temp_aggregation.items():
            max_situation = max(data["situations"]) if data["situations"] else 0.0
            sum_loans = sum(data["loans"]) if data["loans"] else 0.0
            final_debtors.append(
                DebtorData(
                    entity_code=data["entity_code"],
                    cuitCuil=cuit,
                    situation=max_situation,
                    loans=sum_loans,
                )
            )

        final_entities: List[EntityData] = []
        for entity, data in entities_temp_aggregation.items():
            sum_loans = sum(data["loans"]) if data["loans"] else 0.0
            final_entities.append(
                EntityData(
                    entity_code=entity,
                    loans=sum_loans
                )
            )

        logger.info(
            f"Agregación completada. {len(final_debtors)} registros de deudores, {len(final_entities)} registros de entidades.")
        return final_debtors, final_entities
