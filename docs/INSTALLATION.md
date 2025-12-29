# Installation Guide

## Prerequisites

- Python 3.8 or higher
- Oracle Instant Client (for Oracle connections)
- SQL Server ODBC Driver (for MSSQL connections)

## Installation Steps

1. Clone the repository:
```bash
git clone <repository-url>
cd P6-Database-Analyzer
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure the application:
```bash
cp config/settings.example.yaml config/settings.yaml
# Edit config/settings.yaml as needed
```

5. Run the application:
```bash
python main.py
```

## Docker Installation

1. Build the Docker image:
```bash
docker build -t p6-analyzer .
```

2. Run the container:
```bash
docker-compose up -d
```

## Database Drivers

### Oracle
Install Oracle Instant Client from Oracle's website and configure the library path.

### MSSQL
Install the ODBC Driver for SQL Server appropriate for your system.

