// Parent–Teacher Communication Portal - Client Interactions

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Sidebar Toggle
    const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
    const portalSidebar = document.querySelector('.portal-sidebar');

    if (sidebarToggleBtn && portalSidebar) {
        sidebarToggleBtn.addEventListener('click', () => {
            portalSidebar.classList.toggle('show');
        });

        // Close sidebar if clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth < 992) {
                if (!portalSidebar.contains(e.target) && !sidebarToggleBtn.contains(e.target)) {
                    portalSidebar.classList.remove('show');
                }
            }
        });
    }

    // 2. Chat auto-scroll to latest message
    const chatBox = document.getElementById('chatMessages');
    if (chatBox) {
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // 3. Quick fill demo credentials (For College Lab Demo / Viva)
    window.fillCredentials = function(email, password) {
        const emailInput = document.getElementById('email');
        const passInput = document.getElementById('password');
        if (emailInput && passInput) {
            emailInput.value = email;
            passInput.value = password;
            // Visual highlight
            emailInput.classList.add('is-valid');
            passInput.classList.add('is-valid');
            setTimeout(() => {
                emailInput.classList.remove('is-valid');
                passInput.classList.remove('is-valid');
            }, 1000);
        }
    };

    // 4. Delete Confirmation Helper
    const deleteButtons = document.querySelectorAll('.btn-confirm-delete');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const itemName = btn.getAttribute('data-item-name') || 'this item';
            if (!confirm(`Are you sure you want to delete ${itemName}? This action cannot be undone.`)) {
                e.preventDefault();
            }
        });
    });

    // 5. Auto dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });
});
