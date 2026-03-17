# CLFL Core Library

Shared Python utilities for Cargo Line projects.

## Installation

### From Artifact Registry (after publishing):
```bash
pip install clfl-core-library --index-url https://us-central1-python.pkg.dev/clfl-core-library/clfl-packages/simple/
```

### Upgrading to a new version:

> **Note:** Use `--no-deps` to avoid pip dependency resolution errors on Python 3.14+. Always pin the version explicitly.

```bash
pip install --upgrade clfl-core-library==<version> --no-deps --index-url https://us-central1-python.pkg.dev/clfl-core-library/clfl-packages/simple/
```

When prompted:
- **Username:** `oauth2accesstoken`
- **Password:** output of `gcloud auth print-access-token`

### Local Development:
```bash
pip install -e /path/to/clfl-core-library
```

## Usage
```python
from clfl_core import DriveManager, extract_year_from_shipment

# Extract year from shipment
year = extract_year_from_shipment('CLFL25-11-204085')  # Returns '2025'

# Use Drive Manager
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file('creds.json')
manager = DriveManager(credentials)

drive_id = manager.get_shared_drive_by_year(2025)
folder = manager.find_shipment_folder('CLFL25-11-204085', drive_id)
```

## Modules

- `drive_utils` - Google Drive operations
- `shipment_utils` - Shipment number parsing
- `auth` - Authentication helpers (future)