document.getElementById('uploadForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const formData = new FormData(this);
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message || data.error);
        loadTasks();  // Refresh task list after upload
    })
    .catch(error => console.error('Error:', error));
});

function loadTasks() {
    fetch('/tasks')
        .then(response => response.json())
        .then(tasks => {
            const taskList = document.getElementById('taskList');
            taskList.innerHTML = '';
            tasks.forEach(task => {
                const div = document.createElement('div');
                div.textContent = `Image: ${task.image_file}, Status: ${task.status}, Model: ${task.model_file || 'N/A'}`;
                taskList.appendChild(div);
            });
        })
        .catch(error => console.error('Error:', error));
}

// Load tasks initially and refresh every 60 seconds
loadTasks();
setInterval(loadTasks, 60000);