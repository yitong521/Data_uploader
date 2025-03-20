# Transaction Data Processing System

A Python web application that processes financial transaction data from various sources (CSV, JSON, XML) and combines them in a unified SQLite database. The system supports asynchronous processing, data validation, and provides a web interface for data management.

## Features

- Accept multiple file formats:
  - CSV files
  - JSON files
  - XML files
- Automatic currency conversion to EUR
- Duplicate transaction detection
- Asynchronous file processing
- Real-time processing status updates
- Search functionality by UTI or ISIN
- Database management capabilities
- Web-based user interface

## Project Structure

```
Flask_API/
├── app/
│   ├── __init__.py          # Flask app initialization
│   ├── data_processing.py   # Core data processing logic
│   ├── tasks.py            # Celery task definitions
│   └── views.py           # Flask routes and views
├── static/
│   ├── styles.css         # CSS styles
│   └── scripts.js         # Frontend JavaScript
├── templates/
│   └── index.html         # Main page template
├── celery_app.py          # Celery configuration
├── app.py                # Application entry point
└── requirements.txt      # Project dependencies
```

## Requirements

- Python 3.10+
- Redis server
- Web browser (Chrome, Firefox, Safari)

### Python Dependencies

```Flask==2.0.1
celery==5.2.7
redis==4.3.4
pandas==1.4.2
pytz==2022.1
Werkzeug==2.0.2
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Flask_API
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install and start Redis server:
- On Ubuntu/Debian:
  ```bash
  sudo apt-get install redis-server
  sudo service redis-server start
  ```
- On Windows:
  Download and install from [Redis Windows](https://github.com/microsoftarchive/redis/releases)

## Running the Application

1. Start Redis server (if not already running)

2. Start Celery worker:
```bash
celery -A celery_app worker --loglevel=info
```

3. Start Flask application:
```bash
python app.py
```

4. Access the web interface at: http://localhost:3000

## Usage Guide

### Uploading Files

1. Click "Choose Files" to select one or more files
2. Supported formats:
   - CSV files with headers: transaction_uti, isin, notional, etc.
   - JSON files with transaction data
   - XML files with transaction elements
3. Click "Upload Files" to start processing
4. Processing status will be shown:
   - Total records processed
   - New records added
   - Duplicate records found

### Viewing Data

- All transactions are displayed in a table below the upload section
- Most recent transactions appear first
- Table shows up to 100 records at a time

### Searching Records

1. Enter UTI or ISIN in the search box
2. Click "Search" to filter records
3. Click "View All" to reset the view

### Database Management

- Click "Reset Database" to clear all records (requires confirmation)
- Database is automatically initialized on first use

## File Format Requirements

### CSV Format
```csv
transaction_uti,isin,notional,notional_currency,transaction_type,transaction_datetime,exchange_rate,legal_entity_identifier
UTI123,DE000A1EWWW8,1000,USD,BUY,2024-03-20 10:00:00,0.92,LEI123456789
```

### JSON Format
```json
{
  "transactions": [
    {
      "transaction_uti": "UTI123",
      "isin": "DE000A1EWWW8",
      "notional": 1000,
      "notional_currency": "USD",
      "transaction_type": "BUY",
      "transaction_datetime": "2024-03-20 10:00:00",
      "exchange_rate": 0.92,
      "legal_entity_identifier": "LEI123456789"
    }
  ]
}
```

### XML Format
```xml
<transactions>
  <transaction>
    <transaction_uti>UTI123</transaction_uti>
    <isin>DE000A1EWWW8</isin>
    <notional>1000</notional>
    <notional_currency>USD</notional_currency>
    <transaction_type>BUY</transaction_type>
    <transaction_datetime>2024-03-20 10:00:00</transaction_datetime>
    <exchange_rate>0.92</exchange_rate>
    <legal_entity_identifier>LEI123456789</legal_entity_identifier>
  </transaction>
</transactions>
```

## Data Processing Details

1. **File Processing**
   - Files are validated for format and content
   - Data is normalized to a common structure
   - Monetary values are converted to EUR using provided exchange rates

2. **Duplicate Handling**
   - Duplicates are identified by transaction_uti
   - New records are added to database
   - Duplicate records are counted but not added

3. **Data Storage**
   - All data is stored in SQLite database
   - Timestamps are in European timezone
   - Monetary values are rounded to 1 decimal place

## Common Issues and Solutions

1. **File Upload Fails**
   - Check file format matches requirements
   - Ensure file size is under 16MB
   - Verify all required fields are present

2. **Processing Errors**
   - Check file encoding (should be UTF-8)
   - Verify date format (YYYY-MM-DD HH:MM:SS)
   - Ensure numerical values are valid

3. **Database Connection Issues**
   - Verify SQLite database file permissions
   - Check disk space availability
   - Ensure no other process is locking the database

4. **Celery Worker Issues**
   - Verify Redis server is running
   - Check Celery worker logs for errors
   - Restart Celery worker if needed

## Security Considerations

- File uploads are validated for type and size
- SQL injection prevention through parameterized queries
- Secure filename handling
- Temporary file cleanup after processing

## Limitations

- Maximum file size: 16MB
- Displays up to 100 records at a time
- Supports only CSV, JSON, and XML formats
- Single database file (SQLite)
