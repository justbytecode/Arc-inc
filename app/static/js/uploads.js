// Upload and import progress tracking
class UploadManager {
    constructor() {
        this.uploadBtn = document.getElementById('upload-btn');
        this.fileInput = document.getElementById('csv-file');
        this.uploadProgress = document.getElementById('upload-progress');
        this.uploadProgressBar = document.getElementById('upload-progress-bar');
        this.uploadProgressText = document.getElementById('upload-progress-text');
        this.importProgress = document.getElementById('import-progress');
        this.importProgressBar = document.getElementById('import-progress-bar');
        this.importProgressText = document.getElementById('import-progress-text');
        this.importStatus = document.getElementById('import-status');
        this.importMessage = document.getElementById('import-message');
        this.retryBtn = document.getElementById('retry-btn');

        this.statsElements = {
            totalRows: document.getElementById('total-rows'),
            processedRows: document.getElementById('processed-rows'),
            importedRows: document.getElementById('imported-rows'),
            updatedRows: document.getElementById('updated-rows'),
            skippedRows: document.getElementById('skipped-rows')
        };

        this.currentJobId = null;
        this.eventSource = null;

        this.init();
    }

    init() {
        this.uploadBtn.addEventListener('click', () => this.startUpload());
        this.retryBtn.addEventListener('click', () => this.startUpload());
    }

    async startUpload() {
        const file = this.fileInput.files[0];

        if (!file) {
            alert('Please select a CSV file');
            return;
        }

        if (!file.name.endsWith('.csv')) {
            alert('Only CSV files are allowed');
            return;
        }

        // Reset UI
        this.resetProgress();
        this.uploadProgress.classList.remove('hidden');
        this.uploadBtn.disabled = true;

        try {
            // Upload file with progress tracking
            const response = await API.uploadFile(file, (percent, loaded, total) => {
                this.updateUploadProgress(percent);
            });

            this.currentJobId = response.job_id;

            // Hide upload progress, show import progress
            this.uploadProgress.classList.add('hidden');
            this.importProgress.classList.remove('hidden');

            // Start SSE connection for import progress
            this.connectToImportProgress(this.currentJobId);

        } catch (error) {
            alert(`Upload failed: ${error.message}`);
            this.uploadBtn.disabled = false;
            this.uploadProgress.classList.add('hidden');
        }
    }

    updateUploadProgress(percent) {
        this.uploadProgressBar.style.width = `${percent}%`;
        this.uploadProgressText.textContent = `${Math.round(percent)}%`;
    }

    connectToImportProgress(jobId) {
        // Poll for status updates (SSE endpoint will be added in backend later)
        // For now, use polling
        this.pollImportStatus(jobId);
    }

    async pollImportStatus(jobId) {
        const pollInterval = setInterval(async () => {
            try {
                const status = await API.request(`/api/imports/${jobId}/status`);
                this.updateImportProgress(status);

                if (status.status === 'completed' || status.status === 'failed') {
                    clearInterval(pollInterval);
                    this.uploadBtn.disabled = false;

                    if (status.status === 'failed') {
                        this.retryBtn.classList.remove('hidden');
                    }
                }
            } catch (error) {
                console.error('Failed to fetch import status:', error);
                clearInterval(pollInterval);
                this.setImportStatus('failed', 'Failed to fetch status');
                this.uploadBtn.disabled = false;
                this.retryBtn.classList.remove('hidden');
            }
        }, 1000);  // Poll every second
    }

    updateImportProgress(status) {
        // Update status badge
        this.setImportStatus(status.status, '');

        // Update progress bar
        const percent = status.total_rows > 0
            ? (status.processed_rows / status.total_rows * 100)
            : 0;
        this.importProgressBar.style.width = `${percent}%`;
        this.importProgressText.textContent = `${Math.round(percent)}%`;

        // Update stats
        this.statsElements.totalRows.textContent = status.total_rows || 0;
        this.statsElements.processedRows.textContent = status.processed_rows || 0;
        this.statsElements.importedRows.textContent = status.imported_rows || 0;
        this.statsElements.updatedRows.textContent = status.updated_rows || 0;
        this.statsElements.skippedRows.textContent = status.skipped_rows || 0;

        // Update message
        if (status.error_message) {
            this.importMessage.textContent = status.error_message;
        } else {
            this.importMessage.textContent = this.getStatusMessage(status.status);
        }
    }

    setImportStatus(status, message) {
        this.importStatus.textContent = status;
        this.importStatus.className = `status-badge ${status.toLowerCase()}`;
        this.importMessage.textContent = message;
    }

    getStatusMessage(status) {
        const messages = {
            'pending': 'Import job created, waiting to start...',
            'uploading': 'Uploading file...',
            'parsing': 'Parsing CSV file...',
            'importing': 'Importing products into database...',
            'completed': 'Import completed successfully!',
            'failed': 'Import failed. Please check the error log.'
        };
        return messages[status] || status;
    }

    resetProgress() {
        this.uploadProgressBar.style.width = '0%';
        this.uploadProgressText.textContent = '0%';
        this.importProgressBar.style.width = '0%';
        this.importProgressText.textContent = '0%';
        this.setImportStatus('pending', '');
        this.retryBtn.classList.add('hidden');

        Object.values(this.statsElements).forEach(el => {
            el.textContent = '0';
        });
    }
}

// Initialize on page load
let uploadManager;
document.addEventListener('DOMContentLoaded', () => {
    uploadManager = new UploadManager();
});
