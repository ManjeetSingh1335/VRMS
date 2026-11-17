// VRMS Frontend JavaScript Utility

// Open modal helper
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

// Close modal helper
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Global modal overlay click-to-close
window.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
});

// Toast notification helper
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type}`;
    toast.style.position = 'fixed';
    toast.style.bottom = '20px';
    toast.style.right = '20px';
    toast.style.zIndex = '9999';
    toast.style.boxShadow = '0 10px 15px -3px rgba(0,0,0,0.1)';
    toast.style.animation = 'modalFadeIn 0.3s ease-out';
    toast.innerHTML = `<span>${message}</span>`;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.4s ease';
        setTimeout(() => toast.remove(), 400);
    }, 4000);
}

// Green Software Metrics Live Poller
async function updateGreenMetrics() {
    try {
        const resp = await fetch('/api/green-metrics');
        const data = await resp.json();
        if (data.success) {
            const m = data.metrics;
            const el = document.getElementById('greenMetricsDisplay');
            if (el) {
                el.innerHTML = `
                    <span title="In-Memory Cache Hits avoiding DB queries">⚡ Cache Hits: <strong>${m.cache_hits}</strong> (${m.cache_hit_ratio_percent}%)</span>
                    <span style="margin: 0 10px;">|</span>
                    <span title="Queries prevented">🌱 DB Reads Avoided: <strong>${m.db_reads_avoided}</strong></span>
                    <span style="margin: 0 10px;">|</span>
                    <span title="Estimated Carbon Saved">🌿 CO₂ Saved: <strong>${m.carbon_saved_estimated_mg} mg</strong></span>
                `;
            }
        }
    } catch (e) {
        // Silently skip if backend is restarting
    }
}

document.addEventListener('DOMContentLoaded', () => {
    updateGreenMetrics();
    // Refresh green metrics every 15 seconds
    setInterval(updateGreenMetrics, 15000);
});
