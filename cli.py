import asyncio
import typer
import logging
from typing_extensions import Annotated

from core.config import MONGO_CONNECTION_STRING, DB_NAME
from core.data_processor import DataProcessor
from core.exceptions import DataImporterError
from core.file_parser import FileParser
from core.repository import MongoRepository
from core.services import DataImportService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = typer.Typer(help="Herramienta CLI para importar datos de deudores y entidades desde archivos TXT.")

file_parser = FileParser()
data_processor = DataProcessor(file_parser=file_parser)
mongo_repo = MongoRepository()

data_import_service = DataImportService(
    parser=file_parser,
    processor=data_processor,
    repository=mongo_repo
)


@app.callback()
def callback():
    """
    Se ejecuta antes de cualquier comando. Muestra la configuración de DB.
    """
    typer.echo(f"Usando MongoDB: {DB_NAME} en {MONGO_CONNECTION_STRING.split('@')[-1]}")


async def _import_file_async(file_path: str):
    """Función auxiliar asíncrona para manejar la lógica del comando."""
    try:
        await mongo_repo.connect()
        summary = await data_import_service.import_data_from_file(file_path)
        typer.secho(f"Resumen de importación para '{file_path}':", fg=typer.colors.GREEN)
        typer.secho(f"  Estado: {summary.get('status', 'desconocido')}", fg=typer.colors.GREEN)
        typer.secho(f"  Deudores guardados: {summary.get('debtors_saved', 0)}", fg=typer.colors.GREEN)
        typer.secho(f"  Entidades guardadas: {summary.get('entities_saved', 0)}", fg=typer.colors.GREEN)
        if "error_message" in summary:
            typer.secho(f"  Error: {summary['error_message']}", fg=typer.colors.RED, err=True)

    except DataImporterError as e:
        typer.secho(f"Error de importación: {e}", fg=typer.colors.RED, err=True)
    except Exception as e:
        typer.secho(f"Error inesperado en CLI: {e}", fg=typer.colors.RED, err=True)
    finally:
        await mongo_repo.disconnect()


@app.command()
def import_file(
    file_path: Annotated[str, typer.Argument(exists=True, file_okay=True, dir_okay=False, readable=True, help="Ruta al archivo TXT a importar.")]
):
    """
    Importa datos desde el archivo TXT especificado.
    """
    typer.echo(f"Procesando archivo: {file_path}")
    asyncio.run(_import_file_async(file_path))


if __name__ == "__main__":
    app()
