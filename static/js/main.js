// ReqCraft AI - Frontend JS

// Auto-dismiss flash messages after 5s
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        document.querySelectorAll('.flash-stack .alert').forEach(el => {
            if (window.bootstrap) {
                const a = bootstrap.Alert.getOrCreateInstance(el);
                a.close();
            }
        });
    }, 5000);

    // Animate score rings into view
    document.querySelectorAll('.score-ring').forEach(ring => {
        const pct = ring.dataset.pct || 0;
        let col = 'var(--indigo)';
        if (pct >= 75) col = 'var(--green)';
        else if (pct >= 50) col = 'var(--amber)';
        else col = 'var(--red)';
        ring.style.setProperty('--col', col);
        let cur = 0;
        const target = parseInt(pct);
        const tick = () => {
            cur += Math.max(1, Math.ceil(target / 30));
            if (cur >= target) cur = target;
            ring.style.setProperty('--pct', cur);
            const valEl = ring.querySelector('.score-ring-value');
            if (valEl) valEl.textContent = cur;
            if (cur < target) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
    });
});

// Loading state on generation form
function setLoading(btn, text) {
    if (!btn) return;
    btn.disabled = true;
    btn.dataset.original = btn.innerHTML;
    btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>${text || 'Working...'}`;
}

// Character counter helper
function bindCounter(textareaId, counterId) {
    const ta = document.getElementById(textareaId);
    const c = document.getElementById(counterId);
    if (!ta || !c) return;
    const update = () => { c.textContent = ta.value.length; };
    ta.addEventListener('input', update);
    update();
}
