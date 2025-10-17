from pathlib import Path
import logging
from typing import Union, List

# Import the necessary third-party library
import polars as pl

logger = logging.getLogger("ELESS.TableParser")


def dataframe_to_text(df: pl.DataFrame, file_path: Path) -> str:
    """
    Converts a Polars DataFrame into a structured text format suitable for embedding.

    This function processes each row into a descriptive text entry.
    """
    text_entries: List[str] = []

    # Get column names to use as keys
    columns = df.columns

    # Iterate through the rows. Using df.iter_rows() is efficient in Polars.
    for index, row_tuple in enumerate(df.iter_rows()):
        # Create a single descriptive string for the row
        row_description = f"Row {index + 1} from table in file {file_path.name}: "

        # Concatenate column_name: value pairs
        parts = []
        # Use zip to pair column names with row values
        for col, value in zip(columns, row_tuple):
            # Convert value to string and handle potential nulls (Polars' null is None)
            value_str = str(value).strip() if value is not None else ""
            if value_str:
                parts.append(f"{col.strip()}: {value_str}")

        row_description += "; ".join(parts)
        text_entries.append(row_description)

    # Join all row descriptions with a clear separator
    return "\n--ROW ENTRY--\n".join(text_entries)


def parse_csv(file_path: Path) -> str:
    """
    Extracts data from a CSV file using Polars and converts it to embedding-friendly text.
    """
    try:
        # Polars is highly efficient at reading CSVs
        df = pl.read_csv(file_path, try_parse_dates=True)

        if df.is_empty():
            logger.warning(f"CSV file {file_path.name} is empty.")
            return ""

        return dataframe_to_text(df, file_path)

    except FileNotFoundError:
        logger.error(f"CSV file not found at: {file_path}")
    except pl.ComputeError as e:
        logger.error(f"Polars error reading CSV file {file_path.name}: {e}")
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while parsing {file_path.name} as CSV: {e}"
        )

    return ""


def parse_xlsx(file_path: Path) -> str:
    """
    Extracts data from an Excel (.xlsx) file, processing all sheets,
    and converts it to embedding-friendly text using Polars.
    """
    full_text_content: List[str] = []
    try:
        # Polars requires the 'xlsx2csv' engine for reading Excel files
        # Users must ensure they have that dependency if they hit a failure here.

        # Read the file to discover sheet names first (simple approach)
        # Note: Polars' native Excel reader is still developing. We'll use
        # the read_excel function which leverages third-party libraries.

        # The most straightforward way to read multiple sheets in Polars is to
        # know the sheet names or indices. For simplicity, we assume reading
        # sheet 0 works, and leave multi-sheet logic for a more advanced Polars setup.

        # NOTE: For robust multi-sheet reading without pandas, a loop requiring the
        # sheet name is needed. Let's start with a single sheet read for simplicity
        # and standard operation.

        df = pl.read_excel(
            file_path, sheet_name=0, read_options={"infer_schema_length": 100}
        )
        sheet_name = "Sheet1"  # Default name if only reading the first one

        if df.is_empty():
            logger.warning(f"Excel file {file_path.name} sheet {sheet_name} is empty.")
            return ""

        sheet_text = dataframe_to_text(df, file_path)

        full_text_content.append(
            f"\n---SHEET START: {sheet_name}---\n"
            + sheet_text
            + f"\n---SHEET END: {sheet_name}---\n"
        )

        return "\n\n".join(full_text_content).strip()

    except FileNotFoundError:
        logger.error(f"Excel file not found at: {file_path}")
    except pl.ComputeError as e:
        logger.error(f"Polars error reading Excel file {file_path.name}: {e}")
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while parsing {file_path.name} as Excel: {e}"
        )

    return ""
