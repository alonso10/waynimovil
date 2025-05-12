class DataImporterError(Exception):
    """Base class for all data importer exceptions."""
    pass

class FileParsingError(DataImporterError):
    """Exception raised for errors in file parsing."""
    pass

class DataProcessingError(DataImporterError):
    """Exception raised for errors in data processing."""
    pass

class RepositoryError(DataImporterError):
    """Exception raised for errors in repository operations."""
    pass