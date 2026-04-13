// =====================
// FRONTEND LOGIC
// =====================

// Alert auto-close after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease-out';
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.style.display = 'none';
            }, 500);
        }, 5000);
    });
});

// Form validation
function validateExpenseForm() {
    const amount = document.getElementById('amount').value;
    const category = document.getElementById('category').value;
    const date = document.getElementById('date').value;
    
    if (!amount || amount <= 0) {
        alert('Please enter a valid amount');
        return false;
    }
    
    if (!category) {
        alert('Please select a category');
        return false;
    }
    
    if (!date) {
        alert('Please select a date');
        return false;
    }
    
    return true;
}

// Confirm delete
function confirmDelete() {
    return confirm('Are you sure you want to delete this expense?');
}

// Add active class to current nav link
document.addEventListener('DOMContentLoaded', function() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-links a');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.style.borderBottom = '2px solid #667eea';
        }
    });
});