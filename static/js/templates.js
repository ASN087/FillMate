document.addEventListener('DOMContentLoaded', function() {
    // 1. Token Management Utilities
    // ----------------------------
    function isTokenExpired(token) {
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            return payload.exp < Date.now() / 1000;
        } catch {
            return true;
        }
    }

    function getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.cookie.match(/csrftoken=([^;]+)/)?.[1];
    }

    function redirectToLogin() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/users/login-page/';
    }

    async function refreshAuthToken() {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
            redirectToLogin();
            return null;
        }

        try {
            const response = await fetch("/api/users/token/refresh/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCSRFToken()
                },
                body: JSON.stringify({ refresh: refreshToken })
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('access_token', data.access);
                return data.access;
            }
            throw new Error('Refresh failed');
        } catch (error) {
            console.error("Token refresh failed:", error);
            redirectToLogin();
            return null;
        }
    }

    async function getValidToken() {
        let token = localStorage.getItem('access_token');
        if (token && !isTokenExpired(token)) {
            return token;
        }
        return await refreshAuthToken();
    }

    // 2. API Wrapper Function
    // -----------------------
    async function makeAuthenticatedRequest(url, options = {}) {
        const token = await getValidToken();
        if (!token) return null;

        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    ...options.headers,
                    'Authorization': `Bearer ${token}`,
                    'X-CSRFToken': getCSRFToken(),
                    'Content-Type': 'application/json'
                }
            });

            if (response.status === 401) {
                redirectToLogin();
                return null;
            }

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            showError(error.message);
            return null;
        }
    }

    // 3. Application State and UI
    // ---------------------------
    window.currentTemplate = null;
    window.appModals = {};

    function initializeModals() {
        const modals = {
            templateModal: document.getElementById('templateModal'),
            optionsModal: document.getElementById('optionsModal'),
            previewModal: document.getElementById('previewModal')
        };

        for (const [key, element] of Object.entries(modals)) {
            if (element) {
                window.appModals[key] = new bootstrap.Modal(element);
            }
        }
    }

    function clearModalBackdrops() {
        document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
        document.body.classList.remove('modal-open');
    }

    function safeHideModal(modalId) {
        const modal = bootstrap.Modal.getInstance(document.querySelector(modalId));
        if (modal) {
            modal.hide();
            setTimeout(clearModalBackdrops, 300);
        }
    }

    function showError(message) {
        const container = document.getElementById('templateContainer');
        if (!container) return;

        container.innerHTML = `
            <div class="col-12">
                <div class="alert alert-danger">
                    ${message || 'An error occurred. Please try again later.'}
                    ${message.includes('expired') ? '<p><a href="/users/login-page">Click here to login again</a></p>' : ''}
                </div>
            </div>
        `;
    }

    // 4. Template Management
    // ----------------------
    async function loadTemplates() {
        const templates = await makeAuthenticatedRequest('/api/documents/templates/');
        if (!templates) return;

        renderTemplates(templates);
    }

    function renderTemplates(templates) {
        const container = document.getElementById('templateContainer');
        if (!container) return;

        container.innerHTML = templates.length ? '' : `
            <div class="col-12 text-center py-5">
                <i class="bi bi-file-earmark-x fs-1 text-muted"></i>
                <h5 class="mt-3">No templates available</h5>
            </div>
        `;

        templates.forEach(template => {
            const col = document.createElement('div');
            col.className = 'col-md-4 mb-4';
            col.innerHTML = `
                <div class="card h-100 template-card" data-id="${template.id}">
                    <div class="card-img-top bg-light d-flex align-items-center justify-content-center" style="height: 160px">
                        <i class="bi bi-file-earmark-word fs-1 text-primary"></i>
                        ${template.is_public ? '<span class="badge bg-success position-absolute top-0 end-0 m-2">Public</span>' : ''}
                    </div>
                    <div class="card-body">
                        <h5 class="card-title">${template.name}</h5>
                        <p class="card-text">${template.placeholders.length} fields</p>
                        ${template.user ? `<small class="text-muted">Uploaded by ${template.user.username}</small>` : ''}
                    </div>
                </div>
            `;
            col.querySelector('.template-card').addEventListener('click', () => showTemplateOptions(template));
            container.appendChild(col);
        });
    }

    function showTemplateOptions(template) {
        window.currentTemplate = template;
        document.getElementById('optionsModalBody').innerHTML = `
            <div class="text-center">
                <h4 class="mb-4">${template.name}</h4>
                <div class="d-grid gap-3">
                    <button class="btn btn-outline-primary btn-lg" onclick="window.openTemplateForm(${template.id})">
                        <i class="bi bi-file-earmark-plus me-2"></i> Create Document
                    </button>
                    <button class="btn btn-outline-primary btn-lg" onclick="window.previewTemplate(${template.id})">
                        <i class="bi bi-eye me-2"></i> Preview Template
                    </button>
                </div>
            </div>
        `;
        window.appModals?.optionsModal?.show();
    }

    // 5. Document Operations
    // ----------------------
    window.openTemplateForm = function(templateId) {
        const form = document.getElementById('documentForm');
        form.innerHTML = '';

        document.getElementById('templateModalLabel').textContent = window.currentTemplate.name;

        window.currentTemplate.placeholders.forEach(placeholder => {
            const formGroup = document.createElement('div');
            formGroup.className = 'form-group mb-3';

            formGroup.innerHTML = `
                <label class="form-label">${placeholder.name.replace(/_/g, ' ').titleize()}</label>
                <input type="${placeholder.type === 'date' ? 'date' : 'text'}" 
                       class="form-control" 
                       name="${placeholder.name}"
                       placeholder="${placeholder.example || ''}"
                       required>
            `;
            form.appendChild(formGroup);
        });

        window.appModals?.optionsModal?.hide();
        window.appModals?.templateModal?.show();
    };

    // --- MODIFY THIS FUNCTION ---
window.handleFormSubmission = async function() {
    const submitBtn = document.getElementById('submitForApprovalBtn');
    const form = document.getElementById('documentForm');
    // Get the dedicated error display area within the modal
    const errorArea = document.getElementById('submissionErrorArea');

    // Clear previous errors and validation states
    if (errorArea) {
        errorArea.textContent = '';
        errorArea.classList.add('d-none');
    }
    form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));

    // --- 1. CLIENT-SIDE VALIDATION ---
    let firstInvalidField = null;
    let allFieldsValid = true;
    // Select all visible input/textarea fields that should be required
    // Adjust selector if you have other types like select
    const requiredFields = form.querySelectorAll('input:not([type="hidden"]):not([type="radio"]):not([type="checkbox"]), textarea');

    requiredFields.forEach(field => {
        if (!field.value.trim()) { // Check if value is empty after trimming whitespace
            allFieldsValid = false;
            field.classList.add('is-invalid'); // Add Bootstrap's invalid class for styling
            if (!firstInvalidField) {
                firstInvalidField = field; // Store the first empty field to focus later
            }
        } else {
            field.classList.remove('is-invalid'); // Remove class if valid
        }
    });

    if (!allFieldsValid) {
        const errorMessage = 'Please fill out all required fields.';
        if (errorArea) {
            errorArea.textContent = errorMessage;
            errorArea.classList.remove('d-none'); // Show the error area
        } else {
            alert(errorMessage); // Fallback to alert
        }
        if (firstInvalidField) {
            firstInvalidField.focus(); // Focus the first invalid field
        }
        // DO NOT disable the submit button here - let the user fix and retry
        return; // Stop the submission process
    }
    // --- END CLIENT-SIDE VALIDATION ---


    // --- 2. If validation passes, proceed with submission ---
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Submitting...';

    const token = await getValidToken(); // Get valid token (handles refresh)
    if (!token) { // If token failed (e.g., refresh failed, redirected)
        submitBtn.disabled = false; // Re-enable button
        submitBtn.innerHTML = '<i class="bi bi-send-check me-2"></i> Submit for Approval';
        // Error message/redirect should be handled by getValidToken/redirectToLogin
        return;
    }

    const formData = new FormData(form);
    const format = document.querySelector('input[name="format"]:checked')?.value || 'docx'; // Safely get format
    formData.append('format', format);

    try {
        // Make sure currentTemplate is available
        if (!window.currentTemplate || !window.currentTemplate.id) {
            throw new Error("Current template data is missing.");
        }

        const response = await fetch(`/api/documents/templates/${window.currentTemplate.id}/submit/`, {
            method: 'POST',
            headers: {
                // 'Content-Type' is set automatically by browser for FormData
                'Authorization': `Bearer ${token}`,
                'X-CSRFToken': getCSRFToken() // Ensure getCSRFToken function is available
            },
            body: formData
        });

        const result = await response.json(); // Try to parse JSON regardless of status

        if (!response.ok) {
            // Use error from backend response if available
            throw new Error(result.error || `Submission failed with status: ${response.status}`);
        }

        // Success - Redirect
        // Maybe show a success message briefly before redirecting?
        window.location.href = result.redirect_url || '/documents/my-documents/'; // Redirect to My Docs page

    } catch (error) {
        console.error('Submission failed:', error);
        const errorMessage = `Submission Failed: ${error.message}`;
         if (errorArea) {
            errorArea.textContent = errorMessage;
            errorArea.classList.remove('d-none'); // Show the error area
        } else {
            alert(errorMessage); // Fallback to alert
        }
        // Re-enable button on error ONLY
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="bi bi-send-check me-2"></i> Submit for Approval';
    }
    // Removed finally block as button state is handled in success (redirect) or catch (error)
};

    window.previewTemplate = async function(templateId) {
        const optionsModalBody = document.getElementById('optionsModalBody');
        optionsModalBody.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-3">Generating preview...</p>
            </div>
        `;

        try {
            const response = await fetch(`/api/documents/templates/${templateId}/preview/`, {
                headers: {
                    'Authorization': `Bearer ${await getValidToken()}`
                }
            });

            if (!response.ok) throw new Error(await response.text() || 'Preview failed');

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const iframe = document.getElementById('previewIframe');
            
            iframe.onload = function() {
                window.appModals?.optionsModal?.hide();
                window.appModals?.previewModal?.show();
            };
            iframe.src = url;
        } catch (error) {
            console.error('Preview error:', error);
            const cleanError = error.message.replace(/<[^>]*>?/gm, '');
            optionsModalBody.innerHTML = `
                <div class="alert alert-danger">
                    <strong>Preview Error:</strong> ${cleanError}
                </div>
                <button class="btn btn-secondary mt-2" onclick="showTemplateOptions(${templateId})">
                    Back to Options
                </button>
            `;
        }
    };

    // 6. Initialize Application
    // -------------------------
    initializeModals();
    loadTemplates();

    // Helper extension
    String.prototype.titleize = function() {
        return this.replace(/\b\w/g, char => char.toUpperCase());
    };
});