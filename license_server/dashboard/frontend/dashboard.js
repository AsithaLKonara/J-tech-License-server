/**
 * Dashboard Frontend JavaScript
 * Handles device management, billing, and account settings
 */

const API_BASE = '/dashboard/api';
const AUTH_TOKEN_KEY = 'auth_token';

class Dashboard {
    constructor() {
        this.authToken = localStorage.getItem(AUTH_TOKEN_KEY);
        this.init();
    }

    async init() {
        // Check authentication
        if (!this.authToken) {
            this.redirectToLogin();
            return;
        }

        // Setup event listeners
        this.setupTabs();
        this.setupLogout();

        // Load initial data
        await this.loadUserInfo();
        await this.loadDevices();
        await this.loadBilling();
        await this.loadEntitlements();
    }

    setupTabs() {
        const tabButtons = document.querySelectorAll('.tab-btn');
        tabButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const tabName = btn.dataset.tab;
                this.switchTab(tabName);
            });
        });
    }

    switchTab(tabName) {
        // Update buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.tab === tabName) {
                btn.classList.add('active');
            }
        });

        // Update content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
            if (content.id === `${tabName}-tab`) {
                content.classList.add('active');
            }
        });
    }

    setupLogout() {
        document.getElementById('logout-btn').addEventListener('click', () => {
            localStorage.removeItem(AUTH_TOKEN_KEY);
            this.redirectToLogin();
        });
    }

    async apiCall(endpoint, options = {}) {
        const url = `${API_BASE}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.authToken}`,
            ...options.headers
        };

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            if (response.status === 401) {
                this.redirectToLogin();
                return null;
            }

            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            return null;
        }
    }

    async loadUserInfo() {
        const data = await this.apiCall('/user');
        if (data) {
            document.getElementById('user-email').textContent = data.email;
        }
    }

    async loadDevices() {
        const data = await this.apiCall('/devices');
        if (!data) return;

        const devicesList = document.getElementById('devices-list');
        if (data.devices.length === 0) {
            devicesList.innerHTML = '<p>No devices registered.</p>';
            return;
        }

        devicesList.innerHTML = data.devices.map(device => `
            <div class="device-card">
                <div class="device-info">
                    <h3>${device.device_name || device.device_id}</h3>
                    <p>Device ID: ${device.device_id}</p>
                    <p>Plan: ${device.plan}</p>
                    <p>Last seen: ${new Date(device.last_seen).toLocaleString()}</p>
                </div>
                <div class="device-actions">
                    <button onclick="dashboard.renameDevice('${device.id}', '${device.device_name || device.device_id}')">Rename</button>
                    <button onclick="dashboard.revokeDevice('${device.id}')" class="danger">Revoke</button>
                </div>
            </div>
        `).join('');
    }

    async revokeDevice(deviceId) {
        if (!confirm('Are you sure you want to revoke this device?')) {
            return;
        }

        const data = await this.apiCall(`/devices/${deviceId}/revoke`, {
            method: 'POST'
        });

        if (data && data.success) {
            alert('Device revoked successfully');
            this.loadDevices();
        }
    }

    async renameDevice(deviceId, currentName) {
        const newName = prompt('Enter new device name:', currentName);
        if (!newName) return;

        const data = await this.apiCall(`/devices/${deviceId}/rename`, {
            method: 'POST',
            body: JSON.stringify({ device_name: newName })
        });

        if (data && data.success) {
            alert('Device renamed successfully');
            this.loadDevices();
        }
    }

    async loadBilling() {
        const data = await this.apiCall('/billing');
        if (!data) return;

        const billingInfo = document.getElementById('billing-info');
        
        if (!data.has_subscription) {
            billingInfo.innerHTML = '<p>No active subscription. <a href="/checkout">Subscribe now</a></p>';
            return;
        }

        billingInfo.innerHTML = `
            <div class="billing-card">
                <h3>Current Plan: ${data.plan}</h3>
                <p>Status: ${data.status}</p>
                ${data.expires_at ? `<p>Expires: ${new Date(data.expires_at).toLocaleDateString()}</p>` : ''}
                <button onclick="dashboard.openBillingPortal()">Manage Subscription</button>
            </div>
        `;
    }

    async openBillingPortal() {
        const data = await this.apiCall('/billing/update-payment', {
            method: 'POST',
            body: JSON.stringify({})
        });
        // This would redirect to Stripe billing portal
    }

    async loadEntitlements() {
        const data = await this.apiCall('/entitlements');
        if (!data) return;

        const entitlementsInfo = document.getElementById('entitlements-info');
        
        if (data.entitlements.length === 0) {
            entitlementsInfo.innerHTML = '<p>No entitlements found.</p>';
            return;
        }

        entitlementsInfo.innerHTML = data.entitlements.map(ent => `
            <div class="entitlement-card">
                <h3>${ent.product_id}</h3>
                <p>Plan: ${ent.plan}</p>
                <p>Status: ${ent.status}</p>
                <p>Features: ${ent.features.join(', ')}</p>
                ${ent.expires_at ? `<p>Expires: ${new Date(ent.expires_at).toLocaleDateString()}</p>` : ''}
            </div>
        `).join('');
    }

    redirectToLogin() {
        window.location.href = '/login';
    }
}

// Initialize dashboard when page loads
let dashboard;
window.addEventListener('DOMContentLoaded', () => {
    dashboard = new Dashboard();
});
