from celery_app import celery
from app.data_processing import process_file
import os

@celery.task(name='app.tasks.process_file_task')
def process_file_task(filepath):
    """异步处理文件的任务"""
    try:
        result = process_file(filepath)
        if os.path.exists(filepath):
            os.remove(filepath)
            
        # 确保返回的数据是可序列化的
        serializable_result = {
            'total_records': int(result['total_records']),  # 确保是原生 Python 类型
            'new_count': int(result['new_count']),
            'duplicate_count': int(result['duplicate_count'])
        }
        
        return {
            'status': 'success',
            'result': serializable_result
        }
        
    except Exception as e:
        print(f"Task error: {str(e)}")
        if os.path.exists(filepath):
            os.remove(filepath)
        return {
            'status': 'error',
            'error': str(e),
            'result': None
        } 