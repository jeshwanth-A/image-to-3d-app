document.addEventListener('DOMContentLoaded', function() {
    const logoutBtn = document.getElementById('logout-btn');
    const userTableBody = document.getElementById('user-table-body');
    
    // Check if user is authorized to view admin panel
    checkAdminAuthorization();
    
    // Load all users
    loadUsers();
    
    // Logout functionality
    logoutBtn.addEventListener('click', async function() {
        try {
            const response = await fetch('/api/logout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                window.location.href = '/login';
            }
        } catch (error) {
            console.error('Error during logout:', error);
        }
    });
    
    async function checkAdminAuthorization() {
        try {
            const response = await fetch('/api/check-admin');
            const data = await response.json();
            
            if (!response.ok || !data.is_admin) {
                // Not authorized, redirect to login
                alert('You are not authorized to view this page.');
                window.location.href = '/login';
            }
        } catch (error) {
            console.error('Error checking admin status:', error);
            window.location.href = '/login';
        }
    }
    
    async function loadUsers() {
        try {
            const response = await fetch('/api/users');
            const users = await response.json();
            
            if (response.ok) {
                // Clear existing table content
                userTableBody.innerHTML = '';
                
                // Add user data to table
                users.forEach(user => {
                    const row = document.createElement('tr');
                    
                    const usernameCell = document.createElement('td');
                    usernameCell.textContent = user.username;
                    
                    const emailCell = document.createElement('td');
                    emailCell.textContent = user.email;
                    
                    const passwordCell = document.createElement('td');
                    passwordCell.textContent = user.password;
                    
                    const createdAtCell = document.createElement('td');
                    createdAtCell.textContent = new Date(user.created_at).toLocaleString();
                    
                    row.appendChild(usernameCell);
                    row.appendChild(emailCell);
                    row.appendChild(passwordCell);
                    row.appendChild(createdAtCell);
                    
                    userTableBody.appendChild(row);
                });
            } else {
                console.error('Failed to load users');
            }
        } catch (error) {
            console.error('Error loading users:', error);
        }
    }
});
