document.addEventListener('DOMContentLoaded', function() {
    // Common elements that might be in the DOM
    const loginBtn = document.getElementById('login-btn');
    const signupBtn = document.getElementById('signup-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const errorMessage = document.getElementById('error-message');
    const userTableBody = document.getElementById('user-table-body');
    
    // Determine current page
    const currentPath = window.location.pathname;
    
    // ======================================
    // LOGIN FUNCTIONALITY
    // ======================================
    if (loginBtn) {
        loginBtn.addEventListener('click', async function() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            // Simple validation
            if (!username || !password) {
                errorMessage.textContent = 'Please fill in all fields';
                return;
            }
            
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ username, password })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    // Login successful
                    errorMessage.textContent = '';
                    
                    // Redirect based on user type
                    if (data.is_admin) {
                        window.location.href = '/admin';
                    } else {
                        window.location.href = '/dashboard';
                    }
                } else {
                    // Login failed
                    errorMessage.textContent = data.message || 'Login failed. Please check your credentials.';
                }
            } catch (error) {
                console.error('Error during login:', error);
                errorMessage.textContent = 'An error occurred. Please try again.';
            }
        });
    }

    // ======================================
    // SIGNUP FUNCTIONALITY
    // ======================================
    if (signupBtn) {
        signupBtn.addEventListener('click', async function() {
            const username = document.getElementById('username').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            // Simple validation
            if (!username || !email || !password) {
                errorMessage.textContent = 'Please fill in all fields';
                return;
            }
            
            if (password.length < 6) {
                errorMessage.textContent = 'Password must be at least 6 characters long';
                return;
            }
            
            try {
                const response = await fetch('/api/signup', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ username, email, password })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    // Signup successful
                    alert('Account created successfully! Please login.');
                    window.location.href = '/login';
                } else {
                    // Signup failed
                    errorMessage.textContent = data.message || 'Signup failed. Please try again.';
                }
            } catch (error) {
                console.error('Error during signup:', error);
                errorMessage.textContent = 'An error occurred. Please try again.';
            }
        });
    }

    // ======================================
    // ADMIN FUNCTIONALITY
    // ======================================
    if (currentPath === '/admin') {
        // Check if user is authorized to view admin panel
        checkAdminAuthorization();
        
        // Load all users
        loadUsers();
        
        // Logout functionality for admin page
        if (logoutBtn) {
            logoutBtn.addEventListener('click', handleLogout);
        }
    }

    // ======================================
    // UTILITY FUNCTIONS
    // ======================================
    
    // Logout functionality (can be used from any page)
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
    
    async function handleLogout() {
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
    }
    
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
        if (!userTableBody) return;
        
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
