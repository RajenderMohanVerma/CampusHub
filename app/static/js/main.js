/**
 * CampusHub Dynamic Frontend Engine (Vanilla JS & Chart.js Helpers)
 */

document.addEventListener("DOMContentLoaded", function () {
  // 1. Theme (Dark / Light Mode) Switching Engine with LocalStorage Persistence
  const themeToggleBtn = document.getElementById("themeToggleBtn");
  const currentTheme = localStorage.getItem("campushub_theme") || "light";
  
  if (currentTheme === "dark") {
    document.documentElement.setAttribute("data-theme", "dark");
    if (themeToggleBtn) {
      themeToggleBtn.innerHTML = '<i class="bi bi-sun-fill text-warning"></i>';
    }
  }

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", function (e) {
      e.preventDefault();
      let theme = document.documentElement.getAttribute("data-theme");
      if (theme === "dark") {
        document.documentElement.removeAttribute("data-theme");
        localStorage.setItem("campushub_theme", "light");
        this.innerHTML = '<i class="bi bi-moon-stars-fill"></i>';
      } else {
        document.documentElement.setAttribute("data-theme", "dark");
        localStorage.setItem("campushub_theme", "dark");
        this.innerHTML = '<i class="bi bi-sun-fill text-warning"></i>';
      }
      // Recompute charts styling on theme change if chart exists
      window.dispatchEvent(new Event("themeChanged"));
    });
  }

  // 2. Animated Sidebar Toggler
  const sidebarToggle = document.getElementById("sidebarToggle");
  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", function (e) {
      e.preventDefault();
      document.body.classList.toggle("sidebar-collapsed");
      const isCollapsed = document.body.classList.contains("sidebar-collapsed");
      localStorage.setItem("sidebar_collapsed", isCollapsed ? "true" : "false");
    });
  }

  // Restore sidebar state
  if (localStorage.getItem("sidebar_collapsed") === "true") {
    if (window.innerWidth > 992) {
      document.body.classList.add("sidebar-collapsed");
    }
  }

  // 3. Initialize Bootstrap Toast Alerts automatically
  const toastElementList = document.querySelectorAll(".toast");
  const toastList = [...toastElementList].map(
    (toastEl) => new bootstrap.Toast(toastEl, { delay: 4500 })
  );
  toastList.forEach((toast) => toast.show());

  // 3b. Small page transition - fade in body
  document.body.style.opacity = 0;
  document.body.style.transition = 'opacity 320ms ease-out';
  requestAnimationFrame(() => { document.body.style.opacity = 1; });

  // 4. Instant Real-time Table Search Filter
  const tableSearchInput = document.getElementById("tableSearchInput");
  if (tableSearchInput) {
    tableSearchInput.addEventListener("keyup", function () {
      const filter = this.value.toLowerCase();
      const rows = document.querySelectorAll("table.table-custom tbody tr");
      
      rows.forEach((row) => {
        const text = row.textContent || row.innerText;
        row.style.display = text.toLowerCase().indexOf(filter) > -1 ? "" : "none";
      });
    });
  }

  // 5. Bootstrap Tooltip & Popover Initialization
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  [...tooltipTriggerList].map((tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl));

  // 6. Dynamic Real-Time Unread Notifications Badge Synchronizer
  const navUnreadBadge = document.getElementById("navUnreadBadge");
  if (navUnreadBadge) {
    fetch("/notifications/api/unread-count")
      .then((response) => response.ok ? response.json() : Promise.reject(response))
      .then((data) => {
        if (data && data.unread_count > 0) {
          navUnreadBadge.textContent = data.unread_count > 99 ? "99+" : data.unread_count;
          navUnreadBadge.classList.remove("d-none");
        } else {
          navUnreadBadge.classList.add("d-none");
        }
      })
      .catch((err) => {
        // Silently swallow fetch failure on unauthenticated or session expiry states
      });
  }

  // 7. Initialize marquee tickers
  const marquees = document.querySelectorAll('.marquee');
  marquees.forEach((m) => {
    if (!m.querySelector('span')) return;
    // pause on hover and resume on leave
    m.addEventListener('mouseenter', () => { m.style.animationPlayState = 'paused'; });
    m.addEventListener('mouseleave', () => { m.style.animationPlayState = 'running'; });
  });

  // 8. Utility: show skeleton for a container for a minimum duration
  window.showSkeleton = function(containerSelector, duration = 600) {
    const container = document.querySelector(containerSelector);
    if (!container) return;
    const skeleton = document.createElement('div');
    skeleton.className = 'skeleton p-3';
    skeleton.style.minHeight = '80px';
    container.prepend(skeleton);
    setTimeout(() => skeleton.remove(), duration);
  };
});
