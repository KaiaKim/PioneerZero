// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    const loginBtn = document.getElementById('btn-siwg');
    if (loginBtn) {
        loginBtn.addEventListener('click', loginSIWG);
    }
    
    // Check if already authenticated
    const googleUser = localStorage.getItem('google_user');
    if (googleUser) {
        try {
            const user = JSON.parse(googleUser);
            const app = document.querySelector('.login');
            if (app) {
                app.innerHTML = `<h3>관리자: ${user.name || user.email} 👋</h3>`;
            }
        } catch (e) {
            console.error('Error parsing stored user:', e);
        }
    }
});
