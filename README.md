# Primavera Database Analyzer

A comprehensive tool for analyzing Oracle and MSSQL Primavera P6 databases. This tool provides:

- **Schema Health Scanning**: Validates database schema integrity
- **Index Fragmentation Analysis**: Identifies fragmented indexes that need maintenance
- **Deadlock Detection**: Monitors and reports database deadlocks
- **Table Analysis**: Identifies large tables and potential warning conditions
- **Corruption Detection**: Scans for data corruption and upgrade inconsistencies
- **Remediation Suggestions**: Provides actionable recommendations for issues found
- **GUI Dashboard**: Modern PySide6-based interface for easy navigation
- **Report Generation**: Export analysis results to HTML and PDF formats

## Installation

1. Install Python 3.8 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. For Oracle connectivity, you may need to install Oracle Instant Client separately.

## Usage

Run the main application:
```bash
python main.py
```

## Features

### Database Connections
- Oracle P6 databases (via cx_Oracle)
- Microsoft SQL Server P6 databases (via pyodbc)

### Analysis Modules
- Schema health validation
- Index fragmentation assessment
- Deadlock monitoring
- Table size and health analysis
- Corruption and upgrade inconsistency detection

### Reporting
- Interactive GUI dashboard
- HTML report export
- PDF report export

## Requirements

- Python 3.8+
- Oracle Instant Client (for Oracle connections)
- SQL Server ODBC Driver (for MSSQL connections)

