import re

def extract_year_from_shipment(shipment_number: str) -> str | None:
    """
    Extracts the year from a Cargo Line shipment number (e.g. 'CLFL26-02-300616' -> '2026')
    """
    match = re.search(r'CLFL(\d{2})-', shipment_number)
    if match:
        return '20' + match.group(1)
    return None
