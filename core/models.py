from pydantic import BaseModel, Field


class RawRecord(BaseModel):
    """
    A class representing a raw record with a single field.
    """

    entity_code_str: str
    cuit_cuil_str: str
    situation_str: str
    total_str: str


class ProcessedRecordData(BaseModel):
    """
    A class representing a processed record with the necessary fields.
    """

    entity_code: int
    cuit_cuil: int
    situation: float
    loans: float

class DebtorData(BaseModel):
    """
    A class representing a debtor with its details.
    """

    entity_code: int
    cuit_cuil: int = Field(..., alias="cuitCuil")
    situation: float = Field(..., alias="situation")
    loans: float = Field(..., alias="loans")

    class Config:
        """
        Pydantic configuration to allow aliasing of fields.
        """
        populate_by_name = True


class EntityData(BaseModel):
    """
    A class representing an entity with its details.
    """

    entity_code: int
    loans: float = Field(..., alias="loans")

    class Config:
        """
        Pydantic configuration to allow aliasing of fields.
        """
        populate_by_name = True