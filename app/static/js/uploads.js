// Upload and import progress tracking
class UploadManager {
    constructor() {
        this.uploadBtn = document.getElementById('upload-btn');
        this.fileInput = document.getElementById('csv-file');
        this.dropZone = document.getElementById('drop-zone');
        this.fileNameDisplay = document.getElementById('file-name');

        this.progressCard = document.getElementById('progress-card');
        this.importProgressBar = document.getElementById('import-progress-bar');
        this.importProgressText = document.getElementById('import-progress-text');
        this.importStatus = document.getElementById('import-status');
        this.importMessage = document.getElementById('import-message');

        this.statsElements = {
            totalRows: document.getElementById('total-rows'),
            processedRows: document.getElementById('processed-rows'),
            importedRows: document.getElementById('imported-rows'),
            updatedRows: document.getElementById('updated-rows'),
            skippedRows: document.getElementById('skipped-rows')
        };

        this.currentJobId = null;
        this.init();
    }

    init() {
        this.uploadBtn.addEventListener('click', () => this.startUpload());

        // File input change
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e.target.files[0]));

        // Drag and drop events
        this.dropZone.addEventListener('click', () => this.fileInput.click());

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, () => {
                this.dropZone.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, () => {
                this.dropZone.classList.remove('dragover');
            });
        });

        this.dropZone.addEventListener('drop', (e) => {
            const file = e.dataTransfer.files[0];
            this.handleFileSelect(file);
        });
    }

    handleFileSelect(file) {
        if (!file) return;

        if (!file.name.endsWith('.csv')) {
            alert('Only CSV files are allowed');
            return;
        }

        this.selectedFile = file;
        this.fileNameDisplay.textContent = file.name;
        this.uploadBtn.disabled = false;

        // Reset progress UI if starting new file
        this.progressCard.classList.add('hidden');
    }

    async startUpload() {
        if (!this.selectedFile) return;

        // Reset UI
        this.resetProgress();
        this.progressCard.classList.remove('hidden');
        this.uploadBtn.disabled = true;
        this.setImportStatus('uploading', 'Uploading file...');

        try {
            // Upload file
            const response = await API.uploadFile(this.selectedFile, (percent) => {
                // We reuse the import progress bar for upload progress initially
                this.updateProgressBar(percent);
                this.importProgressText.textContent = `Uploading: ${Math.round(percent)}%`;
            });

            this.currentJobId = response.job_id;

            // Start polling for import progress
            this.pollImportStatus(this.currentJobId);

        } catch (error) {
            alert(`Upload failed: ${error.message}`);
            this.uploadBtn.disabled = false;
            this.setImportStatus('failed', error.message);
        }
    }

    updateProgressBar(percent) {
        this.importProgressBar.style.width = `${percent}%`;
    }

    async pollImportStatus(jobId) {
        const pollInterval = setInterval(async () => {
            try {
                const status = await API.request(`/api/imports/${jobId}/status`);
                this.updateImportProgress(status);

                if (status.status === 'completed' || status.status === 'failed') {
                    clearInterval(pollInterval);
                    this.uploadBtn.disabled = false;
                    this.fileNameDisplay.textContent = 'Select new file';
                    this.selectedFile = null;
                }
            } catch (error) {
                console.error('Failed to fetch import status:', error);
                clearInterval(pollInterval);
                this.setImportStatus('failed', 'Failed to fetch status');
                this.uploadBtn.disabled = false;
            }
        }, 1000);
    }

    updateImportProgress(status) {
        this.setImportStatus(status.status, this.getStatusMessage(status.status));

        const percent = status.total_rows > 0
            ? (status.processed_rows / status.total_rows * 100)
            : 0;

        this.updateProgressBar(percent);
        this.importProgressText.textContent = `${Math.round(percent)}%`;

        // Update stats
        this.statsElements.totalRows.textContent = status.total_rows || 0;
        this.statsElements.processedRows.textContent = status.processed_rows || 0;
        this.statsElements.importedRows.textContent = status.imported_rows || 0;
        this.statsElements.updatedRows.textContent = status.updated_rows || 0;
        this.statsElements.skippedRows.textContent = status.skipped_rows || 0;

        if (status.error_message) {
            this.importMessage.textContent = status.error_message;
        }
    }

    setImportStatus(status, message) {
        this.importStatus.textContent = status;
        // Remove old status classes
        this.importStatus.className = 'status-badge';
        this.importStatus.classList.add(status.toLowerCase());

        if (message) {
            this.importMessage.textContent = message;
        }
    }

    getStatusMessage(status) {
        const messages = {
            'pending': 'Initializing import job...',
            'uploading': 'Uploading CSV file...',
            'parsing': 'Analyzing CSV structure...',
            'importing': 'Processing records...',
            'completed': 'Import completed successfully',
            'failed': 'Import process failed'
        };
        return messages[status] || status;
    }

    resetProgress() {
        this.updateProgressBar(0);
        this.importProgressText.textContent = '0%';
        this.setImportStatus('pending', 'Ready to start');

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
