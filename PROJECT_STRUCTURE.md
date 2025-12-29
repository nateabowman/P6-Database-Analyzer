# Project Structure

## Directory Layout

```
P6 Database Analyzer/
├── database/              # Database connection modules
│   ├── __init__.py
│   ├── oracle_connector.py    # Oracle database connector
│   ├── mssql_connector.py     # MSSQL database connector
│   └── db_factory.py          # Factory for creating connectors
│
├── analyzers/            # Analysis modules
│   ├── __init__.py
│   ├── schema_health.py       # Schema health scanner
│   ├── index_fragmentation.py # Index fragmentation checker
│   ├── deadlock_detector.py   # Deadlock detection
│   ├── table_analyzer.py      # Table size and health analysis
│   ├── corruption_detector.py # Corruption and upgrade detection
│   └── remediation_engine.py  # Remediation suggestion generator
│
├── gui/                  # GUI components
│   ├── __init__.py
│   └── main_window.py         # Main PySide6 GUI window
│
├── reports/              # Report generators
│   ├── __init__.py
│   ├── html_report.py        # HTML report generator
│   └── pdf_report.py         # PDF report generator
│
├── main.py               # Application entry point
├── requirements.txt      # Python dependencies
├── README.md            # Project documentation
└── .gitignore          # Git ignore file
```

## Key Components

### Database Connectors
- **OracleConnector**: Handles Oracle database connections using cx_Oracle
- **MSSQLConnector**: Handles SQL Server connections using pyodbc
- **DatabaseFactory**: Creates appropriate connector based on database type

### Analysis Modules
- **SchemaHealthScanner**: Validates schema integrity, checks constraints, indexes
- **IndexFragmentationChecker**: Analyzes index fragmentation levels
- **DeadlockDetector**: Monitors and detects database deadlocks
- **TableAnalyzer**: Analyzes table sizes and identifies warning conditions
- **CorruptionDetector**: Detects data corruption and upgrade inconsistencies
- **RemediationEngine**: Generates prioritized remediation plans

### GUI
- **MainWindow**: PySide6-based GUI with:
  - Database connection panel
  - Analysis options selection
  - Results display in tabs
  - Export functionality

### Reports
- **HTMLReportGenerator**: Creates styled HTML reports using Jinja2
- **PDFReportGenerator**: Creates PDF reports using ReportLab

## Usage Flow

1. Launch application: `python main.py`
2. Enter database connection details
3. Select analysis types to run
4. Click "Run Analysis"
5. Review results in GUI tabs
6. Export reports as HTML or PDF

## Database Requirements

### Oracle
- Oracle Instant Client installed
- cx_Oracle library
- Appropriate database permissions

### MSSQL
- SQL Server ODBC Driver
- pyodbc library
- Appropriate database permissions

