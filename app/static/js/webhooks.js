// Webhook management functionality
class WebhookManager {
    constructor() {
        this.init();
    }

    init() {
        // Actions
        document.getElementById('create-webhook-btn').addEventListener('click', () => this.openWebhookModal());

        // Modal controls
        document.querySelector('#webhook-modal .modal-close').addEventListener('click', () => this.closeWebhookModal());
        document.querySelector('#webhook-modal .modal-cancel').addEventListener('click', () => this.closeWebhookModal());
        document.getElementById('webhook-form').addEventListener('submit', (e) => this.saveWebhook(e));

        // Close modal on outside click
        document.getElementById('webhook-modal').addEventListener('click', (e) => {
            if (e.target.id === 'webhook-modal') {
                this.closeWebhookModal();
            }
        });

        // Load webhooks initially
        this.loadWebhooks();
    }

    async loadWebhooks() {
        try {
            const webhooks = await API.request('/api/webhooks');
            this.renderWebhooks(webhooks);
        } catch (error) {
            alert(`Failed to load webhooks: ${error.message}`);
        }
    }

    renderWebhooks(webhooks) {
        const container = document.getElementById('webhooks-list');

        if (webhooks.length === 0) {
            container.innerHTML = '<p>No webhooks configured.</p>';
            return;
        }

        const table = `
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>URL</th>
                        <th>Events</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${webhooks.map(webhook => `
                        <tr>
                            <td>${this.escapeHtml(webhook.name)}</td>
                            <td>${this.escapeHtml(webhook.url)}</td>
                            <td>${webhook.events.join(', ')}</td>
                            <td>${webhook.enabled ? '<span style="color: green;">Enabled</span>' : '<span style="color: red;">Disabled</span>'}</td>
                            <td>
                                <button class="btn-primary" onclick="webhookManager.openWebhookModal(${webhook.id})">Edit</button>
                                <button class="btn-secondary" onclick="webhookManager.testWebhook(${webhook.id})">Test</button>
                                <button class="btn-secondary" onclick="webhookManager.viewLogs(${webhook.id})">Logs</button>
                                <button class="btn-danger" onclick="webhookManager.deleteWebhook(${webhook.id})">Delete</button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        container.innerHTML = table;
    }

    async openWebhookModal(webhookId = null) {
        const modal = document.getElementById('webhook-modal');
        const title = document.getElementById('webhook-modal-title');
        const form = document.getElementById('webhook-form');

        form.reset();
        document.getElementById('webhook-id').value = '';

        // Uncheck all event checkboxes
        document.querySelectorAll('input[name="events"]').forEach(cb => cb.checked = false);

        if (webhookId) {
            title.textContent = 'Edit Webhook';
            try {
                const webhook = await API.request(`/api/webhooks/${webhookId}`);
                document.getElementById('webhook-id').value = webhook.id;
                document.getElementById('webhook-name').value = webhook.name;
                document.getElementById('webhook-url').value = webhook.url;
                document.getElementById('webhook-secret').value = webhook.hmac_secret || '';
                document.getElementById('webhook-enabled').checked = webhook.enabled;

                // Check event boxes
                webhook.events.forEach(event => {
                    const checkbox = document.querySelector(`input[name="events"][value="${event}"]`);
                    if (checkbox) checkbox.checked = true;
                });
            } catch (error) {
                alert(`Failed to load webhook: ${error.message}`);
                return;
            }
        } else {
            title.textContent = 'Create Webhook';
        }

        modal.classList.remove('hidden');
    }

    closeWebhookModal() {
        document.getElementById('webhook-modal').classList.add('hidden');
    }

    async saveWebhook(e) {
        e.preventDefault();

        const webhookId = document.getElementById('webhook-id').value;
        const events = Array.from(document.querySelectorAll('input[name="events"]:checked'))
            .map(cb => cb.value);

        if (events.length === 0) {
            alert('Please select at least one event');
            return;
        }

        const webhookData = {
            name: document.getElementById('webhook-name').value,
            url: document.getElementById('webhook-url').value,
            events: events,
            hmac_secret: document.getElementById('webhook-secret').value || null,
            enabled: document.getElementById('webhook-enabled').checked
        };

        try {
            if (webhookId) {
                await API.request(`/api/webhooks/${webhookId}`, {
                    method: 'PUT',
                    body: JSON.stringify(webhookData)
                });
            } else {
                await API.request('/api/webhooks', {
                    method: 'POST',
                    body: JSON.stringify(webhookData)
                });
            }

            this.closeWebhookModal();
            this.loadWebhooks();
        } catch (error) {
            alert(`Failed to save webhook: ${error.message}`);
        }
    }

    async deleteWebhook(webhookId) {
        if (!confirm('Are you sure you want to delete this webhook?')) {
            return;
        }

        try {
            await API.request(`/api/webhooks/${webhookId}`, { method: 'DELETE' });
            this.loadWebhooks();
        } catch (error) {
            alert(`Failed to delete webhook: ${error.message}`);
        }
    }

    async testWebhook(webhookId) {
        try {
            const result = await API.request(`/api/webhooks/${webhookId}/test`, {
                method: 'POST'
            });

            if (result.success) {
                alert(`Webhook test successful!\nStatus: ${result.status_code}\nResponse time: ${result.response_time_ms}ms`);
            } else {
                alert(`Webhook test failed: ${result.error}`);
            }
        } catch (error) {
            alert(`Failed to test webhook: ${error.message}`);
        }
    }

    async viewLogs(webhookId) {
        try {
            const logs = await API.request(`/api/webhooks/${webhookId}/logs`);

            if (logs.length === 0) {
                alert('No delivery logs found for this webhook.');
                return;
            }

            const logText = logs.map(log =>
                `[${log.created_at}] ${log.event_type} - Attempt ${log.attempt}/${log.max_attempts}\n` +
                `Status: ${log.status_code || 'N/A'}\n` +
                `${log.error_message || 'Success'}\n` +
                `${log.delivered_at ? 'Delivered: ' + log.delivered_at : 'Pending'}\n`
            ).join('\n---\n\n');

            alert(`Webhook Delivery Logs:\n\n${logText}`);
        } catch (error) {
            alert(`Failed to load logs: ${error.message}`);
        }
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize on page load
let webhookManager;
document.addEventListener('DOMContentLoaded', () => {
    webhookManager = new WebhookManager();
});
