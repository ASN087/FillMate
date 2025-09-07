// sidebar.js - New Implementation
document.addEventListener('DOMContentLoaded', function() {
    const toggler = document.querySelector(".toggler-btn");
    
    // Initialize from localStorage
    if (localStorage.getItem('sidebarCollapsed') === 'true') {
        document.querySelector("#sidebar").classList.add("collapsed");
    }
    
    // Toggle sidebar
    if (toggler) {
        toggler.addEventListener("click", function() {
            const sidebar = document.querySelector("#sidebar");
            sidebar.classList.toggle("collapsed");
            localStorage.setItem('sidebarCollapsed', sidebar.classList.contains("collapsed"));
        });
    }
    
    // Auto-collapse on mobile
    function handleResize() {
        if (window.innerWidth < 768) {
            document.querySelector("#sidebar").classList.add("collapsed");
        }
    }
    
    window.addEventListener('resize', handleResize);
    handleResize();
});