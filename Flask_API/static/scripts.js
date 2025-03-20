document.getElementById('uploadForm').onsubmit = function(e) {
    e.preventDefault();
    
    const formData = new FormData();
    const fileInput = document.getElementById('files');
    const files = fileInput.files;
    
    if (files.length === 0) {
        const responseDiv = document.getElementById('response');
        responseDiv.textContent = 'Please select at least one file';
        responseDiv.className = 'error';
        return;
    }
    
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }
    
    // 清除之前的消息
    const responseDiv = document.getElementById('response');
    responseDiv.textContent = 'Uploading files...';
    responseDiv.className = '';
    
    // 添加一个对象来跟踪总统计
    window.totalStats = {
        total_records: 0,
        new_records: 0,
        duplicate_records: 0,
        completed_tasks: 0,
        total_tasks: 0
    };
    
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            responseDiv.innerHTML = `
                <div class="processing">
                    <h3>Processing files...</h3>
                    <p>Please wait while your files are being processed.</p>
                </div>
            `;
            window.totalStats.total_tasks = data.tasks.length;
            data.tasks.forEach(task => pollTaskStatus(task.task_id, task.filename));
        } else {
            throw new Error(data.message);
        }
    })
    .catch(error => {
        responseDiv.textContent = `Upload failed: ${error.message}`;
        responseDiv.className = 'error';
    });
    
    fileInput.value = '';
};

function updateTotalStats(result) {
    window.totalStats.total_records += result.total_records;
    window.totalStats.new_records += result.new_count;
    window.totalStats.duplicate_records += result.duplicate_count;
    window.totalStats.completed_tasks += 1;
    
    if (window.totalStats.completed_tasks === window.totalStats.total_tasks) {
        const responseDiv = document.getElementById('response');
        responseDiv.innerHTML = `
            <div class="total-stats">
                <h3>Total Statistics</h3>
                <ul>
                    <li>Total records processed: ${window.totalStats.total_records}</li>
                    <li>Total new records: ${window.totalStats.new_records}</li>
                    <li>Total duplicate records: ${window.totalStats.duplicate_records}</li>
                </ul>
            </div>
        `;
        viewDatabase();
    }
}

function pollTaskStatus(taskId, filename) {
    const pollInterval = setInterval(() => {
        fetch(`/task_status/${taskId}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success' && data.result) {
                    clearInterval(pollInterval);
                    updateTotalStats(data.result);
                } else if (data.status === 'error') {
                    clearInterval(pollInterval);
                    const responseDiv = document.getElementById('response');
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'file-error';
                    errorDiv.innerHTML = `
                        <h3>File: ${filename}</h3>
                        <p class="error-message">Error: ${data.error}</p>
                    `;
                    responseDiv.appendChild(errorDiv);
                    window.totalStats.completed_tasks += 1;
                }
            })
            .catch(error => {
                clearInterval(pollInterval);
                const responseDiv = document.getElementById('response');
                const errorDiv = document.createElement('div');
                errorDiv.className = 'file-error';
                errorDiv.innerHTML = `
                    <h3>File: ${filename}</h3>
                    <p class="error-message">Error: ${error.message}</p>
                `;
                responseDiv.appendChild(errorDiv);
                window.totalStats.completed_tasks += 1;
            });
    }, 1000);
}

function displayData(data, columns) {
    const tableContainer = document.getElementById('tableContainer');
    if (!data || data.length === 0) {
        tableContainer.innerHTML = '<p>No data available</p>';
        return;
    }

    let table = '<table><thead><tr>';
    columns.forEach(column => {
        table += `<th>${column}</th>`;
    });
    table += '</tr></thead><tbody>';
    
    data.forEach(row => {
        table += '<tr>';
        columns.forEach(column => {
            let value = row[column];
            if (typeof value === 'number') {
                value = value.toLocaleString();
            }
            table += `<td>${value || ''}</td>`;
        });
        table += '</tr>';
    });
    
    table += '</tbody></table>';
    tableContainer.innerHTML = table;
}

function viewDatabase() {
    fetch('/view_database')
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            document.getElementById('stats').textContent = 
                `Total records in database: ${data.total_records}`;
            displayData(data.data, data.columns);
        } else {
            throw new Error(data.message);
        }
    })
    .catch(error => {
        document.getElementById('response').textContent = 'Error loading database content: ' + error;
        document.getElementById('response').className = 'error';
    });
}

function searchDatabase() {
    const searchTerm = document.getElementById('searchInput').value;
    if (!searchTerm) {
        viewDatabase();
        return;
    }
    
    fetch(`/search?q=${encodeURIComponent(searchTerm)}`)
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            document.getElementById('stats').textContent = 
                `Found ${data.total_records} matching records`;
            displayData(data.data, data.columns);
        } else {
            throw new Error(data.message);
        }
    })
    .catch(error => {
        document.getElementById('response').textContent = 'Error: ' + error;
        document.getElementById('response').className = 'error';
    });
}

function resetDatabase() {
    if (confirm('Are you sure you want to reset the database? This will delete all records.')) {
        fetch('/reset_database', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                document.getElementById('response').textContent = data.message;
                document.getElementById('response').className = 'success';
                viewDatabase();
            } else {
                throw new Error(data.message);
            }
        })
        .catch(error => {
            document.getElementById('response').textContent = 'Error: ' + error;
            document.getElementById('response').className = 'error';
        });
    }
}

viewDatabase(); 