"""Converter for New York Supreme Court / county-clerk judgment exports.

These are ``.xls`` files (Crystal Reports output) with a report-style layout
very different from the LexisNexis grid: a header row then repeating multi-row
blocks, one block per judgment. Relevant source columns (0-indexed):

    C  (2)   Index #          -- an integer starts a new judgment block
    M  (12)  Date/Time Filed  -- "YYYY/MM/DD HHMM"
    V  (21)  Amount           -- numeric
    AE (30)  "Plaintiff:" / "Defendant:" label
    AK (36)  name (on a label row) or address (on the following row)

Plaintiff = creditor; each Defendant = a debtor. One output row per defendant,
all sharing the claim's creditor, amount, date and index number.
"""
import os
import re

from django.utils import timezone

from excel_conv.lib.mailmerge import format_dollars, write_mail_merge

# Source-sheet column indices (0-indexed).
COL_INDEX = 2     # C
COL_DATE = 12     # M
COL_AMOUNT = 21   # V
COL_LABEL = 30    # AE
COL_NAME = 36     # AK

_DATE_RE = re.compile(r"^\d{4}/\d{2}/\d{2}")


def _cell(rows, r, c):
    """Safe cell access -> value or None when out of range."""
    if 0 <= r < len(rows) and 0 <= c < len(rows[r]):
        return rows[r][c]
    return None


def _as_index(value):
    """Return the judgment index as an int when the cell holds one, else None."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value) if value > 0 and float(value).is_integer() else None
    text = str(value).strip().replace(",", "")
    return int(text) if text.isdigit() else None


def _date_part(value):
    """'2025/02/11' from '2025/02/11 1032'; '' when not a date."""
    if value and _DATE_RE.match(str(value)):
        return str(value).split()[0]
    return ""


def _parse_nysc_address(text):
    """('street', 'city', 'state', 'zip') from 'street\\nCity, ST Zip'."""
    if not text:
        return "", "", "", ""
    lines = [line.strip() for line in str(text).splitlines() if line.strip()]
    if not lines:
        return "", "", "", ""
    street = lines[0]
    city = state = zip_code = ""
    if len(lines) >= 2:
        city_state_zip = lines[1]
        if ", " in city_state_zip:
            city, rest = city_state_zip.split(", ", 1)
            parts = rest.split()
            if parts:
                state = parts[0]
                if len(parts) > 1:
                    zip_code = parts[1]
        else:
            city = city_state_zip
    return street, city.strip(), state.strip(), zip_code.strip()


def _extract_filing_office(rows):
    """The county-clerk name from the report header (e.g. 'Westchester County Clerk')."""
    for r in range(min(len(rows), 5)):
        for value in rows[r]:
            text = str(value or "").strip()
            if "county clerk" in text.lower():
                return text
    return ""


def _record(defendant, plaintiff, amount, date_filed, index_val, filing_office):
    name, street, city, state, zip_code = defendant
    return {
        "name": name,
        "ADDRESS_1": street,
        "City": city,
        "State": state,
        "Zip": zip_code,
        "Creditor": plaintiff,
        "Judgment": format_dollars(amount),
        "FilingDate": date_filed,
        "JudgmentType": "",
        "FilingNumber": str(index_val),
        "FilingDate2": "",
        "BookPage": "",
        "FilingOffice": filing_office,
    }


def extract_nysc_records(rows, filing_office=""):
    """Parse the report rows into mail-merge record dicts (one per defendant)."""
    records = []
    n = len(rows)
    r = 0
    while r < n:
        index_val = _as_index(_cell(rows, r, COL_INDEX))
        if index_val is None:
            r += 1
            continue

        # Start of a judgment block.
        date_filed = _date_part(_cell(rows, r, COL_DATE))
        amount = _cell(rows, r, COL_AMOUNT)
        plaintiff = ""
        defendants = []

        rr = r
        while rr < n:
            if rr != r and _as_index(_cell(rows, rr, COL_INDEX)) is not None:
                break  # next judgment block
            label = str(_cell(rows, rr, COL_LABEL) or "").strip().lower()
            if "plaintiff" in label:
                plaintiff = str(_cell(rows, rr, COL_NAME) or "").strip()
            elif "defendant" in label:
                name = str(_cell(rows, rr, COL_NAME) or "").strip()
                street, city, state, zip_code = _parse_nysc_address(
                    _cell(rows, rr + 1, COL_NAME)
                )
                defendants.append((name, street, city, state, zip_code))
                rr += 1  # the address row has been consumed
            rr += 1

        for defendant in defendants or [("", "", "", "", "")]:
            records.append(
                _record(defendant, plaintiff, amount, date_filed, index_val, filing_office)
            )
        r = rr
    return records


def _read_xls_rows(path):
    """Read the first sheet of an .xls file into a list of row lists."""
    import xlrd

    book = xlrd.open_workbook(path)
    sheet = book.sheet_by_index(0)
    return [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]


def detect_nysc(path):
    """True if path looks like an NY Supreme Court / county-clerk .xls export."""
    if not str(path).lower().endswith(".xls"):
        return False
    try:
        rows = _read_xls_rows(path)
    except Exception:
        return False
    for r in range(min(len(rows), 30)):
        if str(_cell(rows, r, COL_INDEX) or "").strip() == "Index #":
            return True
        label = str(_cell(rows, r, COL_LABEL) or "").strip().lower()
        if label.startswith("plaintiff") or label.startswith("defendant"):
            return True
    return False


def convert_nysc_sheet(object):
    """Convert an NY Supreme Court .xls judgment export to the mail-merge sheet."""
    source_path = object.excel_file.path
    base = os.path.splitext(source_path)[0].replace("excel_files", "conv_files")
    out_file_path = base + "_converted.xlsx"
    try:
        rows = _read_xls_rows(source_path)
        records = extract_nysc_records(rows, _extract_filing_office(rows))
        write_mail_merge(records, out_file_path)

        conv_name = os.path.splitext(object.excel_file.name)[0] + "_converted.xlsx"
        object.conv_file.name = conv_name.replace("excel_files", "conv_files")
        object.conv_at = timezone.now()
        object.success = True
        object.error = None
        object.save()
        return True
    except Exception as e:
        object.error = str(e)[:300]
        object.success = False
        object.save()
        return False
