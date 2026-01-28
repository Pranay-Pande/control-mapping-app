/**
 * Control Mapping Application - Premium Dashboard UI
 * Complete rewrite for new dashboard layout
 */

// State management
const state = {
    uploadId: null,
    configurationId: null,
    batchId: null,
    jobIds: [],
    jobs: {},
    filename: null,
    providers: [],
    selectedProviders: [],
    frameworkName: null,
    currentStep: 1,      // Currently viewing step
    maxReachedStep: 1    // Highest step user has reached (for navigation permissions)
};

// Provider logo mapping using Simple Icons CDN
const providerLogos = {
    'aws': 'https://cdn.simpleicons.org/amazonwebservices/FF9900',
    'azure': 'https://cdn.simpleicons.org/microsoftazure/0078D4',
    'gcp': 'https://cdn.simpleicons.org/googlecloud/4285F4',
    'kubernetes': 'https://cdn.simpleicons.org/kubernetes/326CE5',
    'github': 'https://cdn.simpleicons.org/github/181717',
    'cloudflare': 'https://cdn.simpleicons.org/cloudflare/F38020',
    'alibabacloud': 'https://cdn.simpleicons.org/alibabacloud/FF6A00',
    'alibaba': 'https://cdn.simpleicons.org/alibabacloud/FF6A00',
    'oracle': 'https://cdn.simpleicons.org/oracle/F80000',
    'oraclecloud': 'https://cdn.simpleicons.org/oracle/F80000',
    'ibm': 'https://cdn.simpleicons.org/ibm/054ADA',
    'vmware': 'https://cdn.simpleicons.org/vmware/607078',
    'docker': 'https://cdn.simpleicons.org/docker/2496ED',
    'terraform': 'https://cdn.simpleicons.org/terraform/7B42BC',
    'hashicorp': 'https://cdn.simpleicons.org/hashicorp/000000',
    'digitalocean': 'https://cdn.simpleicons.org/digitalocean/0080FF',
    'heroku': 'https://cdn.simpleicons.org/heroku/430098',
    'netlify': 'https://cdn.simpleicons.org/netlify/00C7B7',
    'vercel': 'https://cdn.simpleicons.org/vercel/000000',
    'gitlab': 'https://cdn.simpleicons.org/gitlab/FC6D26',
    'bitbucket': 'https://cdn.simpleicons.org/bitbucket/0052CC',
    'jenkins': 'https://cdn.simpleicons.org/jenkins/D24939',
    'circleci': 'https://cdn.simpleicons.org/circleci/343434',
    'datadog': 'https://cdn.simpleicons.org/datadog/632CA6',
    'newrelic': 'https://cdn.simpleicons.org/newrelic/008C99',
    'splunk': 'https://cdn.simpleicons.org/splunk/000000',
    'elastic': 'https://cdn.simpleicons.org/elastic/005571',
    'mongodb': 'https://cdn.simpleicons.org/mongodb/47A248',
    'postgresql': 'https://cdn.simpleicons.org/postgresql/4169E1',
    'mysql': 'https://cdn.simpleicons.org/mysql/4479A1',
    'redis': 'https://cdn.simpleicons.org/redis/DC382D',
    'nginx': 'https://cdn.simpleicons.org/nginx/009639',
    'apache': 'https://cdn.simpleicons.org/apache/D22128',
    'linux': 'https://cdn.simpleicons.org/linux/FCC624',
    'windows': 'https://cdn.simpleicons.org/windows/0078D6',
    'm365': 'https://cdn.simpleicons.org/microsoft365/D83B01',
    'microsoft365': 'https://cdn.simpleicons.org/microsoft365/D83B01',
    'slack': 'https://cdn.simpleicons.org/slack/4A154B',
    'okta': 'https://cdn.simpleicons.org/okta/007DC1',
    'auth0': 'https://cdn.simpleicons.org/auth0/EB5424',
    'crowdstrike': 'https://cdn.simpleicons.org/crowdstrike/F80000',
    'paloaltonetworks': 'https://cdn.simpleicons.org/paloaltonetworks/F04E23',
    'fortinet': 'https://cdn.simpleicons.org/fortinet/EE3124',
    'cisco': 'https://cdn.simpleicons.org/cisco/1BA0D7',
    'snowflake': 'https://cdn.simpleicons.org/snowflake/29B5E8',
    'databricks': 'https://cdn.simpleicons.org/databricks/FF3621',
    'salesforce': 'https://cdn.simpleicons.org/salesforce/00A1E0',
    'sap': 'https://cdn.simpleicons.org/sap/0FAAFF',
    'workday': 'https://cdn.simpleicons.org/workday/005CB9',
    'servicenow': 'https://cdn.simpleicons.org/servicenow/62D84E',
    'jira': 'https://cdn.simpleicons.org/jira/0052CC',
    'confluence': 'https://cdn.simpleicons.org/confluence/172B4D',
    'notion': 'https://cdn.simpleicons.org/notion/000000',
    'airtable': 'https://cdn.simpleicons.org/airtable/18BFFF',
    'twilio': 'https://cdn.simpleicons.org/twilio/F22F46',
    'stripe': 'https://cdn.simpleicons.org/stripe/008CDD',
    'shopify': 'https://cdn.simpleicons.org/shopify/7AB55C',
    'zoom': 'https://cdn.simpleicons.org/zoom/2D8CFF',
    'dropbox': 'https://cdn.simpleicons.org/dropbox/0061FF',
    'box': 'https://cdn.simpleicons.org/box/0061D5'
};

// DOM Elements - will be populated on init
let elements = {};

// Initialize application
async function init() {
    cacheElements();
    setupNavigation();
    setupUploadZone();
    setupConfigForm();
    setupCollapsibles();
    setupToggle();
    setupProcessControls();
    setupExportControls();
    await loadProviders();
    setupAnimations();
}

// Cache DOM elements
function cacheElements() {
    elements = {
        // Navigation
        navItems: document.querySelectorAll('.nav-item'),
        stepPanels: document.querySelectorAll('.step-panel'),

        // Upload
        uploadZone: document.getElementById('upload-zone'),
        fileInput: document.getElementById('file-input'),
        uploadProgress: document.getElementById('upload-progress'),
        uploadSuccess: document.getElementById('upload-success'),
        previewPanel: document.getElementById('preview-panel'),
        previewContent: document.getElementById('preview-content'),
        successFilename: document.getElementById('success-filename'),
        changeFileBtn: document.getElementById('change-file'),
        progressRingFill: document.querySelector('.progress-ring-fill'),
        progressText: document.querySelector('.progress-text'),
        fileName: document.querySelector('.file-preview .file-name'),
        fileSize: document.querySelector('.file-preview .file-size'),

        // Config
        frameworkName: document.getElementById('framework-name'),
        frameworkVersion: document.getElementById('framework-version'),
        frameworkFullName: document.getElementById('framework-full-name'),
        frameworkDescription: document.getElementById('framework-description'),
        providerList: document.getElementById('provider-list'),
        providerSummary: document.getElementById('provider-summary'),
        selectAllProviders: document.getElementById('select-all-providers'),
        saveConfigBtn: document.getElementById('save-config'),
        configStatus: document.getElementById('config-status'),
        enableSubGroup: document.getElementById('enableSubGroup'),
        subgroupRow: document.getElementById('subgroup-row'),
        fieldMappingsToggle: document.getElementById('field-mappings-toggle'),
        fieldMappingsContent: document.getElementById('field-mappings-content'),

        // Process
        summaryFramework: document.getElementById('summary-framework'),
        summaryFile: document.getElementById('summary-file'),
        summaryProviders: document.getElementById('summary-providers'),
        startMappingBtn: document.getElementById('start-mapping'),
        processActions: document.getElementById('process-actions'),
        providersDashboard: document.getElementById('providers-dashboard'),
        overallProgressBar: document.getElementById('overall-progress-bar'),
        overallProgressText: document.getElementById('overall-progress-text'),
        jobsCompleted: document.getElementById('jobs-completed'),
        jobsTotal: document.getElementById('jobs-total'),
        progressMessage: document.getElementById('progress-message'),
        mappingError: document.getElementById('mapping-error'),
        errorMessage: document.getElementById('error-message'),
        retryMappingBtn: document.getElementById('retry-mapping'),

        // Export
        statControls: document.getElementById('stat-controls'),
        statMapped: document.getElementById('stat-mapped'),
        statProviders: document.getElementById('stat-providers'),
        exportSubtitle: document.getElementById('export-subtitle'),
        downloadZipBtn: document.getElementById('download-zip'),
        downloadFiles: document.getElementById('download-files'),
        startNewBtn: document.getElementById('start-new')
    };
}

// Navigation
function setupNavigation() {
    elements.navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const step = parseInt(item.dataset.step);
            // Allow navigation to any step up to maxReachedStep
            if (step <= state.maxReachedStep) {
                goToStep(step);
            }
        });
    });
}

function goToStep(stepNumber) {
    state.currentStep = stepNumber;
    updateNavigation();

    // Update panels with transition
    elements.stepPanels.forEach(panel => {
        panel.classList.remove('active');
    });

    const targetPanel = document.getElementById(`step-${stepNumber}`);
    targetPanel.classList.add('active');

    // Trigger step animations
    if (typeof triggerStepAnimations === 'function') {
        setTimeout(() => triggerStepAnimations(stepNumber), 50);
    }
}

// Advance to a new step (increases maxReachedStep)
function advanceToStep(stepNumber) {
    if (stepNumber > state.maxReachedStep) {
        state.maxReachedStep = stepNumber;
    }
    goToStep(stepNumber);
}

// Update navigation visual state
function updateNavigation() {
    elements.navItems.forEach(item => {
        const itemStep = parseInt(item.dataset.step);
        item.classList.remove('active', 'completed', 'locked');

        if (itemStep === state.currentStep) {
            // Currently viewing step (highest priority)
            item.classList.add('active');
        } else if (itemStep > state.maxReachedStep) {
            // Locked future steps
            item.classList.add('locked');
        } else if (itemStep < state.maxReachedStep) {
            // Completed steps (already passed, but not currently viewing)
            item.classList.add('completed');
        }
        // Step equal to maxReachedStep but not currentStep: accessible, no special styling
    });
}

// Upload Zone
function setupUploadZone() {
    const zone = elements.uploadZone;

    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
        zone.classList.add('dragover');
    });

    zone.addEventListener('dragleave', () => {
        zone.classList.remove('dragover');
    });

    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        zone.classList.remove('dragover');

        if (e.dataTransfer.files.length > 0) {
            // IMPORTANT: Store file reference immediately - DataTransfer becomes invalid after event
            const file = e.dataTransfer.files[0];
            console.log('File dropped:', file.name, file.size);

            // Add success animation before handling upload
            zone.classList.add('drop-success');
            setTimeout(() => {
                zone.classList.remove('drop-success');
                handleFileUpload(file);
            }, 400);
        }
    });

    zone.addEventListener('click', () => {
        elements.fileInput.click();
    });

    elements.fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    elements.changeFileBtn?.addEventListener('click', (e) => {
        e.stopPropagation();
        resetUpload();
    });
}

async function handleFileUpload(file) {
    console.log('Starting upload for:', file.name);

    // Validate file exists
    if (!file) {
        console.error('No file provided to handleFileUpload');
        alert('No file selected');
        return;
    }

    // Show progress section
    elements.uploadZone.style.display = 'none';
    elements.uploadProgress.classList.remove('hidden');
    elements.uploadSuccess.classList.add('hidden');

    // Update file info
    if (elements.fileName) elements.fileName.textContent = file.name;
    if (elements.fileSize) elements.fileSize.textContent = formatFileSize(file.size);

    // Initialize progress ring
    const circumference = 100.53; // 2 * PI * 16
    updateProgressRing(0, circumference);

    // Animate progress ring
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress = Math.min(progress + 5, 90);
        updateProgressRing(progress, circumference);
    }, 100);

    const formData = new FormData();
    formData.append('file', file);

    try {
        console.log('Sending upload request...');
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        clearInterval(progressInterval);
        console.log('Upload response status:', response.status);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Upload failed with status ${response.status}`);
        }

        const data = await response.json();
        console.log('Upload successful:', data);

        // Complete progress animation
        updateProgressRing(100, circumference);

        // Store state
        state.uploadId = data.upload_id;
        state.filename = data.filename;

        // Show success after brief delay
        setTimeout(() => {
            showUploadSuccess(data);
        }, 300);

    } catch (error) {
        clearInterval(progressInterval);
        console.error('Upload error:', error);
        alert(`Upload failed: ${error.message}`);
        resetUpload();
    }
}

function updateProgressRing(progress, circumference) {
    const offset = circumference - (progress / 100) * circumference;
    if (elements.progressRingFill) {
        elements.progressRingFill.style.strokeDashoffset = offset;
    }
    if (elements.progressText) {
        elements.progressText.textContent = `${Math.round(progress)}%`;
    }
}

function showUploadSuccess(data) {
    elements.uploadProgress.classList.add('hidden');
    elements.uploadSuccess.classList.remove('hidden');
    elements.successFilename.textContent = data.filename;

    // Show preview if available
    if (data.preview) {
        elements.previewPanel.classList.remove('hidden');
        elements.previewContent.textContent = data.preview;
    }

    // Auto-advance to configure step
    setTimeout(() => {
        advanceToStep(2);
    }, 800);
}

function resetUpload() {
    elements.uploadZone.style.display = 'flex';
    elements.uploadProgress.classList.add('hidden');
    elements.uploadSuccess.classList.add('hidden');
    elements.previewPanel.classList.add('hidden');
    elements.fileInput.value = '';
    state.uploadId = null;
    state.filename = null;

    // Reset progress ring to 0%
    const circumference = 100.53;
    updateProgressRing(0, circumference);
}

// Provider Loading
async function loadProviders() {
    try {
        const response = await fetch('/providers');
        const data = await response.json();
        state.providers = data.providers;
        renderProviderCards();
    } catch (error) {
        console.error('Failed to load providers:', error);
    }
}

function renderProviderCards() {
    elements.providerList.innerHTML = '';

    state.providers.forEach(provider => {
        const card = document.createElement('div');
        card.className = 'provider-card';
        card.dataset.provider = provider.name;

        // Get provider icon HTML (logo or fallback avatar)
        const iconHtml = getProviderIconHtml(provider.name, provider.display_name);

        card.innerHTML = `
            <input type="checkbox" value="${provider.name}">
            ${iconHtml}
            <div class="provider-info">
                <span class="provider-name">${provider.display_name}</span>
                <span class="provider-checks">${provider.check_count} checks</span>
            </div>
            <div class="provider-check">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                    <polyline points="20 6 9 17 4 12"/>
                </svg>
            </div>
        `;

        card.addEventListener('click', () => toggleProvider(card, provider.name));
        elements.providerList.appendChild(card);
    });

    // Setup select all
    elements.selectAllProviders.addEventListener('change', (e) => {
        const cards = elements.providerList.querySelectorAll('.provider-card');
        cards.forEach(card => {
            const checkbox = card.querySelector('input');
            checkbox.checked = e.target.checked;
            card.classList.toggle('selected', e.target.checked);
        });
        updateProviderSummary();
    });
}

// Get provider icon HTML - returns logo if available, otherwise fallback avatar
function getProviderIconHtml(providerName, displayName) {
    const normalizedName = providerName.toLowerCase().replace(/[\s_-]/g, '');
    const initials = getProviderInitials(displayName);

    // Check for logo match
    let logoUrl = null;
    for (const [key, url] of Object.entries(providerLogos)) {
        if (url && (normalizedName.includes(key) || key.includes(normalizedName))) {
            logoUrl = url;
            break;
        }
    }

    if (logoUrl) {
        // Return logo with hidden fallback that shows on error
        return `
            <div class="provider-icon provider-logo-container">
                <img
                    src="${logoUrl}"
                    alt="${displayName}"
                    class="provider-logo"
                    onerror="this.style.display='none'; this.nextElementSibling.style.display='flex'; this.parentElement.classList.add('show-fallback');"
                >
                <span class="provider-avatar-fallback" style="display:none;">${initials}</span>
            </div>
        `;
    } else {
        // Return letter avatar fallback
        return `
            <div class="provider-icon provider-avatar">
                ${initials}
            </div>
        `;
    }
}

function getProviderInitials(name) {
    return name.split(/[\s_-]/).map(w => w[0]).join('').substring(0, 2).toUpperCase();
}

function toggleProvider(card, providerName) {
    const checkbox = card.querySelector('input');
    checkbox.checked = !checkbox.checked;
    card.classList.toggle('selected', checkbox.checked);
    updateProviderSummary();
}

function updateProviderSummary() {
    const selected = elements.providerList.querySelectorAll('.provider-card.selected');
    const count = selected.length;
    let totalChecks = 0;

    selected.forEach(card => {
        const provider = state.providers.find(p => p.name === card.dataset.provider);
        if (provider) totalChecks += provider.check_count;
    });

    state.selectedProviders = Array.from(selected).map(card => card.dataset.provider);

    if (count === 0) {
        elements.providerSummary.textContent = 'Select at least one provider';
        elements.configStatus.textContent = 'Select providers to continue';
    } else {
        elements.providerSummary.textContent = `${count} provider${count > 1 ? 's' : ''} selected · ${totalChecks.toLocaleString()} total checks`;
        elements.configStatus.textContent = 'Ready to save configuration';
    }

    // Update select all checkbox state
    const allCards = elements.providerList.querySelectorAll('.provider-card');
    elements.selectAllProviders.checked = count === allCards.length;
    elements.selectAllProviders.indeterminate = count > 0 && count < allCards.length;
}

// Collapsible sections
function setupCollapsibles() {
    elements.fieldMappingsToggle?.addEventListener('click', () => {
        elements.fieldMappingsToggle.classList.toggle('collapsed');
        elements.fieldMappingsContent.classList.toggle('collapsed');
    });
}

// Toggle for subgroup
function setupToggle() {
    elements.enableSubGroup?.addEventListener('change', () => {
        if (elements.subgroupRow) {
            elements.subgroupRow.style.display = elements.enableSubGroup.checked ? 'grid' : 'none';
        }
    });
}

// Config Form
function setupConfigForm() {
    elements.saveConfigBtn?.addEventListener('click', saveConfiguration);
}

async function saveConfiguration() {
    if (state.selectedProviders.length === 0) {
        alert('Please select at least one provider');
        return;
    }

    if (!elements.frameworkName.value.trim()) {
        alert('Please enter a framework name');
        elements.frameworkName.focus();
        return;
    }

    state.frameworkName = elements.frameworkName.value.trim();

    const config = {
        upload_id: state.uploadId,
        framework_name: state.frameworkName,
        framework_version: elements.frameworkVersion.value || null,
        framework_full_name: elements.frameworkFullName.value || null,
        framework_description: elements.frameworkDescription.value || null,
        providers: state.selectedProviders,
        enable_subgroup: elements.enableSubGroup?.checked ?? true,
        field_mappings: {
            id_field: document.getElementById('id-field')?.value || null,
            name_field: document.getElementById('name-field')?.value || null,
            description_field: document.getElementById('description-field')?.value || null,
            section_field: document.getElementById('section-field')?.value || null,
            subsection_field: document.getElementById('subsection-field')?.value || null,
            subgroup_field: document.getElementById('subgroup-field')?.value || null,
            service_field: document.getElementById('service-field')?.value || null,
            id_format_example: document.getElementById('id-format-example')?.value || null,
            name_format_example: document.getElementById('name-format-example')?.value || null,
            section_format_example: document.getElementById('section-format-example')?.value || null,
            subsection_format_example: document.getElementById('subsection-format-example')?.value || null,
            subgroup_format_example: document.getElementById('subgroup-format-example')?.value || null,
            description_format_example: document.getElementById('description-format-example')?.value || null
        },
        custom_instructions: document.getElementById('custom-instructions')?.value || null
    };

    elements.saveConfigBtn.disabled = true;
    elements.configStatus.textContent = 'Saving configuration...';

    try {
        const response = await fetch('/configure', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Configuration failed');
        }

        const data = await response.json();
        state.configurationId = data.configuration_id;

        // Update process step summary
        elements.summaryFramework.textContent = state.frameworkName;
        elements.summaryFile.textContent = state.filename;
        elements.summaryProviders.textContent = state.selectedProviders.length + ' providers';

        // Setup provider dashboard cards
        setupProviderDashboard();

        advanceToStep(3);

    } catch (error) {
        alert(`Configuration failed: ${error.message}`);
    } finally {
        elements.saveConfigBtn.disabled = false;
        elements.configStatus.textContent = 'Ready to save configuration';
    }
}

// Process Controls
function setupProcessControls() {
    elements.startMappingBtn?.addEventListener('click', startMapping);
    elements.retryMappingBtn?.addEventListener('click', startMapping);
}

function setupProviderDashboard() {
    elements.providersDashboard.innerHTML = '';
    elements.jobsTotal.textContent = state.selectedProviders.length;

    state.selectedProviders.forEach(providerName => {
        const provider = state.providers.find(p => p.name === providerName);
        const card = document.createElement('div');
        card.className = 'provider-status-card glass-card';
        card.id = `status-${providerName}`;
        card.innerHTML = `
            <div class="provider-status-ring" id="ring-${providerName}">
                <svg viewBox="0 0 64 64">
                    <circle class="ring-bg" cx="32" cy="32" r="28"/>
                    <circle class="ring-fill" cx="32" cy="32" r="28"/>
                </svg>
                <span class="provider-status-icon">⏳</span>
            </div>
            <span class="provider-status-name">${provider?.display_name || providerName}</span>
            <span class="provider-status-text">Pending</span>
        `;
        elements.providersDashboard.appendChild(card);
    });
}

async function startMapping() {
    elements.processActions.classList.add('hidden');
    elements.mappingError.classList.add('hidden');
    elements.providersDashboard.classList.remove('hidden');

    try {
        const response = await fetch('/map', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                upload_id: state.uploadId,
                configuration_id: state.configurationId
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to start mapping');
        }

        const data = await response.json();
        state.batchId = data.batch_id;
        state.jobIds = data.job_ids;
        state.jobs = {};

        data.jobs.forEach(job => {
            state.jobs[job.job_id] = {
                provider: job.provider,
                status: job.status
            };
        });

        pollBatchStatus();

    } catch (error) {
        showMappingError(error.message);
    }
}

async function pollBatchStatus() {
    try {
        const response = await fetch(`/batch/${state.batchId}/status`);
        const data = await response.json();

        updateProgressDisplay(data);

        if (data.status === 'completed') {
            showResults(data);
        } else if (data.status === 'failed') {
            showMappingError(data.error_message || 'Some jobs failed');
        } else {
            setTimeout(pollBatchStatus, 2000);
        }

    } catch (error) {
        showMappingError(`Status check failed: ${error.message}`);
    }
}

function updateProgressDisplay(data) {
    // Overall progress
    const progress = data.overall_progress || 0;
    elements.overallProgressBar.style.width = `${progress}%`;
    elements.overallProgressText.textContent = `${progress}%`;

    const completed = data.jobs.filter(j => j.status === 'completed').length;
    elements.jobsCompleted.textContent = completed;
    elements.progressMessage.textContent = data.current_message || 'Processing...';

    // Update individual provider cards
    data.jobs.forEach(job => {
        updateProviderStatusCard(job);
    });
}

function updateProviderStatusCard(job) {
    const card = document.getElementById(`status-${job.provider}`);
    if (!card) return;

    const ring = card.querySelector('.provider-status-ring');
    const icon = card.querySelector('.provider-status-icon');
    const text = card.querySelector('.provider-status-text');
    const ringFill = card.querySelector('.ring-fill');

    // Update ring progress
    const circumference = 175.93; // 2 * PI * 28
    const progress = job.progress_percentage || 0;
    const offset = circumference - (progress / 100) * circumference;
    ringFill.style.strokeDashoffset = offset;

    // Update status
    ring.classList.remove('completed', 'error');

    if (job.status === 'completed') {
        ring.classList.add('completed');
        icon.textContent = '✓';
        text.textContent = 'Complete';
        ringFill.style.strokeDashoffset = 0;
    } else if (job.status === 'running') {
        icon.textContent = '⚡';
        text.textContent = `${progress}%`;
    } else if (job.status === 'failed') {
        ring.classList.add('error');
        icon.textContent = '✕';
        text.textContent = 'Failed';
    } else {
        icon.textContent = '⏳';
        text.textContent = 'Pending';
    }
}

function showMappingError(message) {
    elements.mappingError.classList.remove('hidden');
    elements.errorMessage.textContent = message;
    elements.processActions.classList.remove('hidden');
}

function showResults(data) {
    // Calculate totals
    let totalControls = 0;
    let controlsWithChecks = 0;

    data.jobs.forEach(job => {
        if (job.summary) {
            totalControls += job.summary.total_controls || 0;
            controlsWithChecks += job.summary.controls_with_checks || 0;
        }
    });

    // Animate stats
    animateCounter(elements.statControls, totalControls);
    animateCounter(elements.statMapped, controlsWithChecks);
    animateCounter(elements.statProviders, data.jobs.length);

    elements.exportSubtitle.textContent = `${data.jobs.length} provider mappings generated successfully`;

    // Populate download files
    elements.downloadFiles.innerHTML = '';
    data.jobs.forEach(job => {
        if (job.status === 'completed') {
            const provider = state.providers.find(p => p.name === job.provider);
            const card = document.createElement('div');
            card.className = 'file-download-card';
            card.innerHTML = `
                <div class="file-download-info">
                    <div class="file-download-icon">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                            <polyline points="14 2 14 8 20 8"/>
                        </svg>
                    </div>
                    <span class="file-download-name">${provider?.display_name || job.provider}</span>
                </div>
                <div class="file-download-actions">
                    <a href="/download/${job.job_id}/json" download>JSON</a>
                    <a href="/download/${job.job_id}/excel" download>Excel</a>
                </div>
            `;
            elements.downloadFiles.appendChild(card);
        }
    });

    advanceToStep(4);
}

// Export Controls
function setupExportControls() {
    elements.downloadZipBtn?.addEventListener('click', () => {
        window.location.href = `/download/batch/${state.batchId}/zip`;
    });

    elements.startNewBtn?.addEventListener('click', resetApplication);
}

function resetApplication() {
    // Reset state
    state.uploadId = null;
    state.configurationId = null;
    state.batchId = null;
    state.jobIds = [];
    state.jobs = {};
    state.filename = null;
    state.selectedProviders = [];
    state.frameworkName = null;
    state.currentStep = 1;
    state.maxReachedStep = 1;

    // Reset upload
    resetUpload();

    // Reset config form
    elements.frameworkName.value = '';
    elements.frameworkVersion.value = '';
    elements.frameworkFullName.value = '';
    elements.frameworkDescription.value = '';

    // Reset field mappings
    ['id-field', 'id-format-example', 'name-field', 'name-format-example',
     'section-field', 'section-format-example', 'subsection-field', 'subsection-format-example',
     'subgroup-field', 'subgroup-format-example', 'description-field', 'description-format-example',
     'service-field', 'custom-instructions'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });

    // Reset providers
    const cards = elements.providerList.querySelectorAll('.provider-card');
    cards.forEach(card => {
        card.classList.remove('selected');
        card.querySelector('input').checked = false;
    });
    elements.selectAllProviders.checked = false;
    elements.selectAllProviders.indeterminate = false;
    updateProviderSummary();

    // Reset process step
    elements.processActions.classList.remove('hidden');
    elements.providersDashboard.innerHTML = '';
    elements.mappingError.classList.add('hidden');
    elements.overallProgressBar.style.width = '0%';
    elements.overallProgressText.textContent = '0%';
    elements.jobsCompleted.textContent = '0';
    elements.progressMessage.textContent = 'Initializing...';

    // Go to step 1
    goToStep(1);
}

// Utility Functions
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function animateCounter(element, target, duration = 1000) {
    if (!element) return;
    const start = 0;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easeProgress = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(start + (target - start) * easeProgress);
        element.textContent = current.toLocaleString();

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

// Animation Enhancements
function setupAnimations() {
    // Setup button ripple effects
    setupButtonRipples();

    // Setup card click animations
    setupCardAnimations();

    // Setup scroll reveal animations
    setupScrollReveal();
}

function setupButtonRipples() {
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            // Create ripple element
            const ripple = document.createElement('span');
            ripple.classList.add('ripple-effect');

            // Calculate position
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            // Style the ripple
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                transform: scale(0);
                animation: rippleEffect 0.6s ease-out forwards;
                pointer-events: none;
            `;

            this.appendChild(ripple);

            // Remove ripple after animation
            setTimeout(() => ripple.remove(), 600);
        });
    });

    // Add ripple animation keyframes dynamically if not exists
    if (!document.querySelector('#ripple-styles')) {
        const style = document.createElement('style');
        style.id = 'ripple-styles';
        style.textContent = `
            @keyframes rippleEffect {
                to {
                    transform: scale(4);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

function setupCardAnimations() {
    // Provider card interactions are now handled purely by CSS
    // No JS manipulation needed - selection is smooth via CSS transitions
    // The :active and :hover states in CSS handle all visual feedback
}

function setupScrollReveal() {
    // Intersection Observer for scroll-triggered animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('revealed');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe elements that should animate on scroll
    document.querySelectorAll('.glass-card, .stat-card, .file-download-card').forEach(el => {
        el.classList.add('scroll-reveal');
        observer.observe(el);
    });
}

// Re-trigger animations when switching steps
function triggerStepAnimations(stepNumber) {
    const panel = document.getElementById(`step-${stepNumber}`);
    if (!panel) return;

    // Re-trigger section animations (but NOT provider cards - they maintain state)
    const sections = panel.querySelectorAll('.config-section, .stat-card');
    sections.forEach((section, index) => {
        // Only re-animate if not already visible
        if (section.style.opacity === '0' || !section.style.opacity) {
            section.style.animationDelay = `${index * 0.05}s`;
        }
    });

    // Provider cards should NOT be re-animated - they maintain their selection state
    // and animate only on initial page load
}

// Initialize on load
document.addEventListener('DOMContentLoaded', init);
