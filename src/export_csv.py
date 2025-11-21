import os
from typing import List, Dict
import json
import pandas as pd
from pathlib import Path
from src.utils import logger

OUTPUT_DIR = "data"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def to_csv(
    records: List[Dict] = None,
    input_json_path: str = "data/processed_news.json",
    filename: str = "final_output.csv"
) -> str:
    """
    Saves a list of dicts OR loads JSON file and saves to CSV.
    Supports:
        to_csv(records=[...])
        to_csv() → auto loads processed_news.json
    """
    # Case 1: No records passed → load JSON
    if records is None:
        json_path = Path(input_json_path)
        if not json_path.exists():
            raise FileNotFoundError(f"Processed JSON file not found: {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            records = json.load(f)

        if not records:
            raise ValueError("Processed JSON is empty. Nothing to export.")

    # Case 2: Save to CSV
    output_path = os.path.join(OUTPUT_DIR, filename)
    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    logger.info("Saved %s records to %s", len(records), output_path)

    return output_path


def to_google_sheets(records: List[Dict], sheet_id: str = None, creds_json: str = None) -> str:
    if not sheet_id:
        sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not creds_json:
        creds_json = os.getenv("GOOGLE_SA_JSON")
    if not sheet_id or not creds_json:
        raise RuntimeError("Google Sheets not configured. Provide sheet_id and service account JSON path.")

    import gspread
    from oauth2client.service_account import ServiceAccountCredentials

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_json, scope)
    client = gspread.authorize(creds)

    sh = client.open_by_key(sheet_id)
    ws = sh.sheet1

    df = pd.DataFrame(records)
    ws.update([df.columns.values.tolist()] + df.values.tolist())

    logger.info("Updated Google Sheet %s with %s rows", sheet_id, len(records))
    return sheet_id
