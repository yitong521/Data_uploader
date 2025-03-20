import pandas as pd
import sqlite3
from datetime import datetime
import json
import xml.etree.ElementTree as ET
import io
import os
import pytz

# Use absolute path pointing to project root directory
DB_PATH = os.path.abspath('transactions.db')

# Set European timezone
EU_TZ = pytz.timezone('Europe/Paris')

def init_database(db_path=DB_PATH):
    """Initialize the database with required schema"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_uti TEXT PRIMARY KEY,
            isin TEXT,
            notional REAL,
            notional_currency TEXT,
            transaction_type TEXT,
            transaction_datetime TEXT,
            exchange_rate REAL,
            legal_entity_identifier TEXT,
            notional_eur REAL,
            source_file TEXT,
            upload_time TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def convert_to_eur(df):
    """Convert monetary values to EUR"""
    if 'notional' in df.columns and 'exchange_rate' in df.columns:
        df['notional'] = pd.to_numeric(df['notional'], errors='coerce')
        df['exchange_rate'] = pd.to_numeric(df['exchange_rate'], errors='coerce')
        df['notional_eur'] = (df['notional'] * df['exchange_rate']).round(1)  # Keep one decimal place
    return df

def process_csv(content):
    """Process CSV file"""
    try:
        df = pd.read_csv(io.BytesIO(content))
        if 'lei' in df.columns:
            df = df.rename(columns={'lei': 'legal_entity_identifier'})
        return convert_to_eur(df)
    except Exception as e:
        print(f"CSV processing error: {str(e)}")
        raise

def process_json(content):
    """Process JSON file"""
    try:
        content_str = content.decode('utf-8')
        data = json.loads(content_str)
        if 'transactions' in data:
            df = pd.json_normalize(data['transactions'])
        else:
            df = pd.json_normalize(data)
        
        if 'lei' in df.columns:
            df = df.rename(columns={'lei': 'legal_entity_identifier'})
        return convert_to_eur(df)
    except Exception as e:
        print(f"JSON processing error: {str(e)}")
        raise

def process_xml(content):
    """Process XML file"""
    try:
        root = ET.fromstring(content)
        data = []
        for transaction in root.findall('.//transaction'):
            transaction_data = {}
            for child in transaction:
                transaction_data[child.tag] = child.text
            data.append(transaction_data)
        
        df = pd.DataFrame(data)
        if 'lei' in df.columns:
            df = df.rename(columns={'lei': 'legal_entity_identifier'})
        return convert_to_eur(df)
    except Exception as e:
        print(f"XML processing error: {str(e)}")
        raise

def process_file(filepath):
    """Process uploaded file and save to database"""
    try:
        # Initialize database
        init_database()
        
        # Read file content
        with open(filepath, 'rb') as f:
            content = f.read()
        
        # Process data based on file type
        if filepath.endswith('.csv'):
            df = process_csv(content)
        elif filepath.endswith('.json'):
            df = process_json(content)
        elif filepath.endswith('.xml'):
            df = process_xml(content)
        else:
            raise ValueError("Unsupported file format")
        
        # Ensure all required columns exist
        required_columns = [
            'transaction_uti', 'isin', 'notional', 'notional_currency',
            'transaction_type', 'transaction_datetime', 'exchange_rate',
            'legal_entity_identifier', 'notional_eur'
        ]
        
        for col in required_columns:
            if col not in df.columns:
                df[col] = None
        
        # Add metadata
        df['source_file'] = filepath
        df['upload_time'] = datetime.now(EU_TZ).strftime('%Y-%m-%d %H:%M')
        
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get existing UTIs
        cursor.execute("SELECT transaction_uti FROM transactions")
        existing_utis = {row[0] for row in cursor.fetchall()}
        
        # Separate new and duplicate records
        new_records = df[~df['transaction_uti'].isin(existing_utis)]
        duplicate_records = df[df['transaction_uti'].isin(existing_utis)]
        
        # Save new records
        if not new_records.empty:
            new_records.to_sql('transactions', conn, if_exists='append', index=False)
        
        conn.commit()
        conn.close()
        
        return {
            'total_records': int(df.shape[0]),
            'new_count': int(len(new_records)),
            'duplicate_count': int(len(duplicate_records))
        }
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        raise Exception(f"Error processing file: {str(e)}")

def update_data_format(db_path=DB_PATH):
    """Update data format in database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Update notional_eur to one decimal place
    cursor.execute("""
        UPDATE transactions 
        SET notional_eur = ROUND(notional_eur, 1)
    """)
    
    # Update upload_time format
    cursor.execute("""
        UPDATE transactions 
        SET upload_time = strftime('%Y-%m-%d %H:%M', upload_time)
    """)
    
    conn.commit()
    conn.close()