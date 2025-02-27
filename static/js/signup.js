document.addEventListener('DOMContentLoaded', function() {
    const signupBtn = document.getElementById('signup-btn');
    const errorMessage = document.getElementById('error-message');
    
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
});
