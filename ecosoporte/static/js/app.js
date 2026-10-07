/* ==========================================================================
   EcoSoporte Digital - Application JavaScript Interactivity
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // Sidebar Elements
  const sidebar = document.getElementById('sidebar');
  const sidebarToggle = document.getElementById('sidebar-toggle');
  const mobileMenuBtn = document.getElementById('mobile-menu-btn');
  const sidebarOverlay = document.getElementById('sidebar-overlay');

  // Load Saved Sidebar Collapse State
  if (sidebar && localStorage.getItem('ecosoporte_sidebar_collapsed') === 'true') {
    sidebar.classList.add('collapsed');
  }

  // Sidebar Collapse Toggle (Desktop)
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', () => {
      sidebar.classList.toggle('collapsed');
      const isCollapsed = sidebar.classList.contains('collapsed');
      localStorage.setItem('ecosoporte_sidebar_collapsed', isCollapsed);
    });
  }

  // Mobile Hamburger Menu Drawer Toggle
  if (mobileMenuBtn && sidebar && sidebarOverlay) {
    const toggleMobileMenu = () => {
      sidebar.classList.toggle('mobile-open');
      sidebarOverlay.classList.toggle('active');
    };

    mobileMenuBtn.addEventListener('click', toggleMobileMenu);
    sidebarOverlay.addEventListener('click', toggleMobileMenu);
  }

  // User Profile Card Dropdown Menu Toggle
  const userDropdownBtn = document.getElementById('user-dropdown-btn');
  const userAvatarBtn = document.getElementById('user-avatar-btn');
  const userDropdownMenu = document.getElementById('user-dropdown-menu');

  if (userDropdownMenu && (userDropdownBtn || userAvatarBtn)) {
    const toggleUserMenu = (e) => {
      e.stopPropagation();
      userDropdownMenu.classList.toggle('show');
    };

    if (userDropdownBtn) userDropdownBtn.addEventListener('click', toggleUserMenu);
    if (userAvatarBtn) userAvatarBtn.addEventListener('click', toggleUserMenu);

    document.addEventListener('click', (e) => {
      if (!userDropdownMenu.contains(e.target)) {
        userDropdownMenu.classList.remove('show');
      }
    });
  }

  // Password Show / Hide Toggle
  const togglePasswordBtns = document.querySelectorAll('.toggle-password-btn');
  togglePasswordBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-target');
      const input = targetId ? document.getElementById(targetId) : btn.previousElementSibling;

      if (input) {
        const isPassword = input.getAttribute('type') === 'password';
        input.setAttribute('type', isPassword ? 'text' : 'password');
        btn.textContent = isPassword ? '👁️‍🗨️' : '👁️';
      }
    });
  });

  // Form Submit Loading State
  const forms = document.querySelectorAll('form:not(.no-loading)');
  forms.forEach(form => {
    form.addEventListener('submit', (e) => {
      const submitBtn = form.querySelector('button[type="submit"], button.btn-primary');
      if (submitBtn && !form.checkValidity || form.checkValidity()) {
        submitBtn.disabled = true;
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '⏳ Procesando...';
      }
    });
  });

  // Auto Dismiss Toast Alerts after 5 seconds
  const toastAlerts = document.querySelectorAll('.toast-alert');
  toastAlerts.forEach(alert => {
    setTimeout(() => {
      alert.style.opacity = '0';
      alert.style.transform = 'translateX(20px)';
      alert.style.transition = 'all 0.3s ease';
      setTimeout(() => alert.remove(), 300);
    }, 5000);
  });
});
