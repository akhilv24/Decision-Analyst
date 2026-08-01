/**
 * Decision Analyst - Main JavaScript
 * Handles client-side logic and interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    initializeDarkMode();
});

function initializeApp() {
    // Initialize tooltips and popovers if using Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize Dark Mode
 */
function initializeDarkMode() {
    // Apply saved theme on page load
    const savedTheme = localStorage.getItem('theme') || 'light';
    applyThemeGlobally(savedTheme);
    
    // Listen for theme changes
    window.addEventListener('themeChanged', function(e) {
        applyThemeGlobally(e.detail.theme);
    });
}

/**
 * Apply theme globally across all pages
 */
function applyThemeGlobally(themeName) {
    document.documentElement.setAttribute('data-theme', themeName);
    document.body.setAttribute('data-theme', themeName);
    localStorage.setItem('theme', themeName);
}

/**
 * Format number as currency
 */
function formatCurrency(value) {
    if (typeof value !== 'number') {
        value = parseFloat(value);
    }
    return '₹' + value.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Format number with commas
 */
function formatNumber(num) {
    if (!num) return '0';
    return parseFloat(num).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

/**
 * Format percentage
 */
function formatPercent(value, decimals = 1) {
    if (typeof value !== 'number') {
        value = parseFloat(value);
    }
    return value.toFixed(decimals) + '%';
}

/**
 * Format date
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

/**
 * Show loading spinner
 */
function showLoading(message = 'Loading...') {
    const loader = document.getElementById('uploadLoader');
    if (loader) {
        loader.style.display = 'block';
        if (message) {
            const p = loader.querySelector('p');
            if (p) p.textContent = message;
        }
    }
}

/**
 * Hide loading spinner
 */
function hideLoading() {
    const loader = document.getElementById('uploadLoader');
    if (loader) {
        loader.style.display = 'none';
    }
}

/**
 * Display success message
 */
function displaySuccess(message) {
    const alertDiv = document.getElementById('successAlert');
    if (alertDiv) {
        const messageSpan = alertDiv.querySelector('#successMessage');
        if (messageSpan) {
            messageSpan.textContent = message;
        }
        alertDiv.style.display = 'block';
        setTimeout(() => {
            alertDiv.style.display = 'none';
        }, 4000);
    }
}

/**
 * Display error message
 */
function displayError(message) {
    const alertDiv = document.getElementById('errorAlert');
    if (alertDiv) {
        const messageSpan = alertDiv.querySelector('#errorMessage');
        if (messageSpan) {
            messageSpan.textContent = message;
        }
        alertDiv.style.display = 'block';
        setTimeout(() => {
            alertDiv.style.display = 'none';
        }, 4000);
    }
}

/**
 * API Call Helper
 */
async function apiCall(endpoint, method = 'GET', data = null) {
    try {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            }
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(endpoint, options);
        const jsonData = await response.json();

        if (!response.ok) {
            throw new Error(jsonData.message || 'API Error');
        }

        return jsonData;
    } catch (error) {
        console.error('API Call Error:', error);
        throw error;
    }
}

/**
 * Validate file type
 */
function isValidFileType(filename) {
    const allowed = ['csv', 'xlsx', 'xls'];
    const ext = filename.split('.').pop().toLowerCase();
    return allowed.includes(ext);
}

/**
 * Validate file size
 */
function isValidFileSize(file, maxSizeMB = 50) {
    return (file.size / 1024 / 1024) <= maxSizeMB;
}

/**
 * Export data as CSV (client-side)
 */
function exportTableToCSV(tableId, filename = 'export.csv') {
    const table = document.getElementById(tableId);
    if (!table) return;

    let csv = [];
    const rows = table.querySelectorAll('tr');

    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = [];
        cols.forEach(col => {
            rowData.push('"' + col.textContent.trim().replace(/"/g, '""') + '"');
        });
        csv.push(rowData.join(','));
    });

    downloadCSV(csv.join('\n'), filename);
}

/**
 * Download CSV file
 */
function downloadCSV(csv, filename) {
    const link = document.createElement('a');
    link.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv);
    link.download = filename;
    link.click();
}

/**
 * Utility: Check if element exists
 */
function elementExists(id) {
    return document.getElementById(id) !== null;
}

/**
 * Utility: Get element by ID safely
 */
function getElement(id) {
    return document.getElementById(id) || null;
}

/**
 * Utility: Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Utility: Throttle function
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Export for use in other scripts
window.DecisionAnalyst = {
    formatCurrency,
    formatNumber,
    formatPercent,
    formatDate,
    showLoading,
    hideLoading,
    displaySuccess,
    displayError,
    apiCall,
    isValidFileType,
    isValidFileSize,
    exportTableToCSV,
    downloadCSV,
    elementExists,
    getElement,
    debounce,
    throttle
};

(function markActiveSidebarLink() {
  const path = (window.location.pathname || '/').replace(/\/+$/, '') || '/';
  const links = document.querySelectorAll('.side-link');

  links.forEach(link => {
    const matchList = (link.dataset.match || link.getAttribute('href') || '')
      .split(',')
      .map(s => s.trim())
      .filter(Boolean);

    const isActive = matchList.some(m => {
      if (m === '/') return path === '/';
      return path === m || path.startsWith(m + '/');
    });

    if (isActive) {
      link.classList.add('active');
      link.setAttribute('aria-current', 'page');
    } else {
      link.classList.remove('active');
      link.removeAttribute('aria-current');
    }
  });
})();
