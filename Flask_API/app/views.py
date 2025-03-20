from app import app
from app.tasks import process_file_task
import os
import sqlite3
import pandas as pd
from werkzeug.utils import secure_filename
from flask import request, jsonify, render_template
from app.data_processing import DB_PATH  # Import unified database path

# Set file upload size limit
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit to 16MB

# Configure upload folder with absolute path
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'temp_uploads')
ALLOWED_EXTENSIONS = {'csv', 'json', 'xml'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def ensure_upload_folder():
    """Ensure upload folder exists"""
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.errorhandler(Exception)
def handle_error(error):
    """Handle all errors and return JSON format"""
    return jsonify({
        'status': 'error',
        'message': str(error)
    }), 500

@app.route('/')
def index():
    try:
        template_path = os.path.join(app.template_folder, 'index.html')
        print(f"Template path: {template_path}")
        print(f"Template exists: {os.path.exists(template_path)}")
        ensure_upload_folder()
        return render_template('index.html')
    except Exception as e:
        print(f"Error rendering template: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload API endpoint"""
    ensure_upload_folder()
    
    try:
        if 'files' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file part'}), 400
        
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return jsonify({'status': 'error', 'message': 'No selected files'}), 400
        
        tasks = []
        for file in files:
            if not allowed_file(file.filename):
                return jsonify({
                    'status': 'error',
                    'message': f'File type not allowed: {file.filename}'
                }), 400
            
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save file
            file.save(filepath)
            
            # Add task to queue
            task = process_file_task.delay(filepath)
            
            tasks.append({
                'task_id': task.id,
                'filename': filename
            })
        
        return jsonify({
            'status': 'success',
            'message': f'Started processing {len(files)} files',
            'tasks': tasks
        }), 202
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/task_status/<task_id>')
def task_status(task_id):
    """Check task status"""
    try:
        task = process_file_task.AsyncResult(task_id)
        print(f"Task state: {task.state}")
        
        if task.ready():
            try:
                result = task.get(timeout=1)
                print(f"Task result: {result}")
                return jsonify(result)
            except Exception as e:
                print(f"Error getting task result: {e}")
                return jsonify({
                    'status': 'error',
                    'error': str(e)
                })
        else:
            return jsonify({
                'status': 'processing',
                'task_id': task_id
            })
    except Exception as e:
        print(f"Task status error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        })

@app.route('/view_database', methods=['GET'])
def view_database():
    """Get database content"""
    try:
        default_columns = [
            'transaction_uti', 'isin', 'notional', 'notional_currency',
            'transaction_type', 'transaction_datetime', 'exchange_rate',
            'legal_entity_identifier', 'notional_eur', 'source_file', 'upload_time'
        ]

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Get total record count
            cursor.execute("SELECT COUNT(*) FROM transactions")
            total_count = cursor.fetchone()[0]
            
            if total_count > 0:
                df = pd.read_sql_query("""
                    SELECT * FROM transactions 
                    ORDER BY upload_time DESC 
                    LIMIT 100
                """, conn)
                data = df.to_dict('records')
            else:
                data = []
            
            conn.close()
            
            return jsonify({
                'status': 'success',
                'total_records': total_count,
                'columns': default_columns,
                'data': data
            }), 200
            
        except sqlite3.OperationalError as e:
            if 'no such table' in str(e):
                return jsonify({
                    'status': 'success',
                    'total_records': 0,
                    'columns': default_columns,
                    'data': []
                }), 200
            raise
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/reset_database', methods=['POST'])
def reset_database():
    """Reset database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM transactions')
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Database reset successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/search', methods=['GET'])
def search_database():
    """Search database content"""
    try:
        search_term = request.args.get('q', '')
        if not search_term:
            return view_database()

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Build search query
            query = """
                SELECT * FROM transactions 
                WHERE transaction_uti LIKE ? 
                   OR isin LIKE ?
                ORDER BY upload_time DESC 
                LIMIT 100
            """
            search_pattern = f'%{search_term}%'
            
            # Execute search
            df = pd.read_sql_query(query, conn, params=(search_pattern, search_pattern))
            total_count = len(df)
            data = df.to_dict('records')
            
            conn.close()
            
            # Return results
            return jsonify({
                'status': 'success',
                'total_records': total_count,
                'columns': [
                    'transaction_uti', 'isin', 'notional', 'notional_currency',
                    'transaction_type', 'transaction_datetime', 'exchange_rate',
                    'legal_entity_identifier', 'notional_eur', 'source_file', 'upload_time'
                ],
                'data': data
            }), 200
            
        except sqlite3.OperationalError as e:
            if 'no such table' in str(e):
                return jsonify({
                    'status': 'success',
                    'total_records': 0,
                    'data': []
                }), 200
            raise
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/favicon.ico')
def favicon():
    return '', 204 