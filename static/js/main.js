/**
 * main.js — EduRankAI Student Management System
 * Client-side interactions and utilities.
 */

/* ── Sidebar Toggle ───────────────────────────────────────────── */
(function () {
  const sidebar = document.getElementById('sidebar');
  const toggleBtn = document.getElementById('sidebarToggle');

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', function () {
      sidebar.classList.toggle('open');
    });

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function (e) {
      if (
        window.innerWidth < 992 &&
        sidebar.classList.contains('open') &&
        !sidebar.contains(e.target) &&
        !toggleBtn.contains(e.target)
      ) {
        sidebar.classList.remove('open');
      }
    });
  }
})();

/* ── Live Date in Topbar ──────────────────────────────────────── */
(function () {
  const dateEl = document.getElementById('currentDate');
  if (!dateEl) return;

  function updateDate() {
    const now = new Date();
    dateEl.textContent = now.toLocaleDateString('en-GB', {
      weekday: 'short',
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  }

  updateDate();
})();

/* ── Auto-dismiss Flash Messages ─────────────────────────────── */
(function () {
  setTimeout(function () {
    document.querySelectorAll('.alert').forEach(function (el) {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      if (bsAlert) bsAlert.close();
    });
  }, 5000);
})();

/* ── Filter form: auto-submit on dropdown change ─────────────── */
(function () {
  ['courseSelect', 'statusSelect'].forEach(function (id) {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('change', function () {
        const form = document.getElementById('filterForm');
        if (form) form.submit();
      });
    }
  });
})();

