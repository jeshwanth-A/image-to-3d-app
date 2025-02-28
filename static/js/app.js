document.addEventListener('DOMContentLoaded', function() {
    // Cache DOM elements
    const elements = {
        loginBtn: document.getElementById('login-btn'),
        signupBtn: document.getElementById('signup-btn'),
        logoutBtn: document.getElementById('logout-btn'),
        errorMessage: document.getElementById('error-message'),
        userTableBody: document.getElementById('user-table-body'),
        currentPath: window.location.pathname
    };
    
    // Initialize functionality based on page context
    initPage(elements);
    
    // Main initialization function
    function initPage(elements) {
        // Login page functionality
        if (elements.loginBtn) {
            elements.loginBtn.addEventListener('click', () => handleLogin(elements));
        }
        
        // Signup page functionality
        if (elements.signupBtn) {
            elements.signupBtn.addEventListener('click', () => handleSignup(elements));
        }
        
        // Admin page functionality
        if (elements.currentPath === '/admin') {
            checkAdminAuthorization();
            loadUsers(elements.userTableBody);
        }
        
        // Logout button (on any page)
        if (elements.logoutBtn) {
            elements.logoutBtn.addEventListener('click', handleLogout);
        }
    }
    
    // Login handler
    async function handleLogin(elements) {
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        
        // Validate input
        if (!username || !password) {
            elements.errorMessage.textContent = 'Please fill in all fields';
            return;
        }
        
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                elements.errorMessage.textContent = '';
                window.location.href = data.is_admin ? '/admin' : '/dashboard';
            } else {
                elements.errorMessage.textContent = data.message || 'Login failed. Please check your credentials.';
            }
        } catch (error) {
            console.error('Error during login:', error);
            elements.errorMessage.textContent = 'An error occurred. Please try again.';
        }
    }
    
    // Signup handler
    async function handleSignup(elements) {
        const username = document.getElementById('username').value.trim();
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        
        // Validate input
        if (!username || !email || !password) {
            elements.errorMessage.textContent = 'Please fill in all fields';
            return;
        }
        
        if (password.length < 6) {
            elements.errorMessage.textContent = 'Password must be at least 6 characters long';
            return;
        }
        
        try {
            const response = await fetch('/api/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, email, password })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                alert('Account created successfully! Please login.');
                window.location.href = '/login';
            } else {
                elements.errorMessage.textContent = data.message || 'Signup failed. Please try again.';
            }
        } catch (error) {
            console.error('Error during signup:', error);
            elements.errorMessage.textContent = 'An error occurred. Please try again.';
        }
    }
    
    // Logout handler
    async function handleLogout() {
        try {
            const response = await fetch('/api/logout', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (response.ok) {
                window.location.href = '/login';
            }
        } catch (error) {
            console.error('Error during logout:', error);
        }
    }
    
    // Admin authorization check
    async function checkAdminAuthorization() {
        try {
            const response = await fetch('/api/check-admin');
            const data = await response.json();
            
            if (!response.ok || !data.is_admin) {
                alert('You are not authorized to view this page.');
                window.location.href = '/login';
            }
        } catch (error) {
            console.error('Error checking admin status:', error);
            window.location.href = '/login';
        }
    }
    
    // Load users table
    async function loadUsers(tableBody) {
        if (!tableBody) return;
        
        try {
            const response = await fetch('/api/users');
            const users = await response.json();
            
            if (response.ok) {
                // Clear and rebuild table
                tableBody.innerHTML = '';
                
                // Create and append user rows
                users.forEach(user => {
                    const row = createUserTableRow(user);
                    tableBody.appendChild(row);
                });
            } else {
                console.error('Failed to load users');
            }
        } catch (error) {
            console.error('Error loading users:', error);
        }
    }
    
    // Create user table row
    function createUserTableRow(user) {
        const row = document.createElement('tr');
        
        // Create cells with user data
        ['username', 'email', 'password'].forEach(field => {
            const cell = document.createElement('td');
            cell.textContent = user[field];
            row.appendChild(cell);
        });
        
        // Add created_at date
        const createdAtCell = document.createElement('td');
        createdAtCell.textContent = new Date(user.created_at).toLocaleString();
        row.appendChild(createdAtCell);
        
        return row;
    }
});
