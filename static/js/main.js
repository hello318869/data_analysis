/**
 * 交互式数据分析系统 — 前端交互增强
 * Progressive enhancement for server-rendered pages
 */
(function () {
    'use strict';

    // ── Flash message auto-dismiss ─────────────────
    function dismissFlashes() {
        document.querySelectorAll('.flash-message').forEach(function (el) {
            el.addEventListener('click', function () {
                el.style.opacity = '0';
                el.style.transition = 'opacity 0.3s';
                setTimeout(function () { el.remove(); }, 300);
            });
        });
    }

    // ── File upload visual feedback ────────────────
    function enhanceFileUploads() {
        document.querySelectorAll('input[type="file"]').forEach(function (input) {
            input.addEventListener('change', function () {
                var label = this.closest('.form-group');
                var nameEl = label ? label.querySelector('.upload-filename') : null;
                if (!nameEl) {
                    nameEl = document.createElement('span');
                    nameEl.className = 'upload-filename';
                    nameEl.style.cssText = 'display:block;margin-top:6px;color:var(--color-gray-500);font-size:0.85rem;';
                    if (label) label.appendChild(nameEl);
                }
                nameEl.textContent = this.files.length ? '已选择: ' + this.files[0].name : '';
            });
        });
    }

    // ── Table row hover ─────────────────────────────
    function enhanceTables() {
        document.querySelectorAll('table tbody tr').forEach(function (row) {
            row.addEventListener('mouseenter', function () {
                this.style.backgroundColor = 'var(--color-primary-light)';
            });
            row.addEventListener('mouseleave', function () {
                this.style.backgroundColor = '';
            });
        });
    }

    // ── Smooth scroll ───────────────────────────────
    function initSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
            anchor.addEventListener('click', function (e) {
                var target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });
    }

    // ── Init on DOM ready ───────────────────────────
    function init() {
        dismissFlashes();
        enhanceFileUploads();
        enhanceTables();
        initSmoothScroll();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
