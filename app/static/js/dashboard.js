// Academic-ScreenX: Light-Mode Dashboard Controller

let currentStatusFilter = 'all';
let currentSearchQuery = '';
let currentSort = 'date_desc';
let pollingTimer = null;

document.addEventListener('DOMContentLoaded', () => {
    initDropzone();
    loadDashboardStats();
    loadSubmissions();
    startPolling();

    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        let debounceTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimeout);
            debounceTimeout = setTimeout(() => {
                currentSearchQuery = e.target.value.trim();
                loadSubmissions();
            }, 250);
        });
    }

    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) {
        sortSelect.addEventListener('change', (e) => {
            currentSort = e.target.value;
            loadSubmissions();
        });
    }
});

function setFilter(status) {
    currentStatusFilter = status;
    document.querySelectorAll('.filter-btn').forEach(btn => {
        if (btn.dataset.status === status) {
            btn.className = 'filter-btn px-3 py-1.5 rounded-md font-semibold transition bg-white text-slate-900 shadow-sm';
        } else {
            btn.className = 'filter-btn px-3 py-1.5 rounded-md font-medium transition text-slate-600 hover:text-slate-900';
        }
    });
    loadSubmissions();
}

async function loadDashboardStats() {
    try {
        const res = await fetch('/api/submissions/stats');
        if (!res.ok) return;
        const stats = await res.json();
        
        const elTotal = document.getElementById('stat-total');
        if (elTotal) elTotal.textContent = stats.total_uploaded;
        
        const elAppPct = document.getElementById('stat-approved-pct');
        if (elAppPct) elAppPct.textContent = `${stats.approved_pct}%`;
        
        const elAppCnt = document.getElementById('stat-approved-count');
        if (elAppCnt) elAppCnt.textContent = `(${stats.approved_count} papers)`;

        const elRevCnt = document.getElementById('stat-revision-count');
        if (elRevCnt) elRevCnt.textContent = stats.revision_count;
        
        const elFlgPct = document.getElementById('stat-flagged-pct');
        if (elFlgPct) elFlgPct.textContent = `${stats.flagged_pct}%`;
        
        const elFlgCnt = document.getElementById('stat-flagged-count');
        if (elFlgCnt) elFlgCnt.textContent = `(${stats.flagged_count} papers)`;
        
        const elAvgTime = document.getElementById('stat-avg-time');
        if (elAvgTime) elAvgTime.textContent = `${stats.avg_processing_time}s`;
    } catch (err) {
        console.error('Error loading stats:', err);
    }
}

async function loadSubmissions() {
    const tableBody = document.getElementById('submissions-table-body');
    const emptyState = document.getElementById('empty-state');
    
    try {
        let url = `/api/submissions/list?sort=${encodeURIComponent(currentSort)}`;
        if (currentStatusFilter !== 'all') {
            url += `&status=${encodeURIComponent(currentStatusFilter)}`;
        }
        if (currentSearchQuery) {
            url += `&q=${encodeURIComponent(currentSearchQuery)}`;
        }

        const res = await fetch(url);
        if (!res.ok) throw new Error('Failed to fetch submissions');
        const submissions = await res.json();

        if (submissions.length === 0) {
            tableBody.innerHTML = '';
            if (emptyState) emptyState.classList.remove('hidden');
            return;
        }

        if (emptyState) emptyState.classList.add('hidden');
        tableBody.innerHTML = submissions.map(sub => renderSubmissionRow(sub)).join('');
    } catch (err) {
        console.error('Error fetching submissions:', err);
    }
}

function renderSubmissionRow(sub) {
    let statusBadge = '';
    if (sub.status === 'approved') {
        statusBadge = `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-sm">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> Approved
        </span>`;
    } else if (sub.status === 'revision') {
        statusBadge = `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200 shadow-sm">
            <span class="w-1.5 h-1.5 rounded-full bg-amber-500"></span> Needs Revision
        </span>`;
    } else if (sub.status === 'flagged') {
        statusBadge = `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200 shadow-sm">
            <span class="w-1.5 h-1.5 rounded-full bg-rose-500"></span> Flagged (Low Novelty)
        </span>`;
    } else if (sub.status === 'processing' || sub.status === 'pending') {
        statusBadge = `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-700 border border-slate-200 pulse-subtle">
            <svg class="animate-spin -ml-0.5 mr-1 h-3 w-3 text-slate-500" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Evaluating...
        </span>`;
    } else {
        statusBadge = `<span class="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-medium bg-slate-100 text-slate-600 border border-slate-200">
            Failed
        </span>`;
    }

    const scoreDisplay = (sub.status === 'processing' || sub.status === 'pending')
        ? '<span class="text-slate-400 font-mono">--</span>'
        : `<div class="flex items-baseline gap-1">
            <span class="font-bold text-sm ${sub.overall_score >= 7.0 ? 'text-emerald-700' : (sub.overall_score >= 4.5 ? 'text-amber-700' : 'text-rose-700')}">
                ${sub.overall_score.toFixed(1)}
            </span>
            <span class="text-slate-400 text-[10px] font-medium">/ 10</span>
           </div>`;

    const compDisplay = sub.compliance_score > 0 ? `<span class="font-semibold text-slate-700">${sub.compliance_score.toFixed(1)}</span><span class="text-slate-400 text-[10px]">/10</span>` : '<span class="text-slate-400 font-mono">--</span>';
    const novDisplay = sub.novelty_score > 0 ? `<span class="font-semibold text-slate-700">${sub.novelty_score.toFixed(1)}</span><span class="text-slate-400 text-[10px]">/10</span>` : '<span class="text-slate-400 font-mono">--</span>';

    return `
    <tr class="hover:bg-slate-50 transition cursor-pointer" onclick="openReportModal(${sub.id})">
        <td class="py-3.5 px-4">
            <div class="flex flex-col">
                <span class="font-semibold text-slate-900 hover:text-sky-700 transition line-clamp-1">${escapeHtml(sub.title)}</span>
                <span class="text-[11px] text-slate-500 mt-0.5 flex items-center gap-1.5">
                    <span>${escapeHtml(sub.student_name || 'Anonymous Applicant')}</span>
                    <span class="text-slate-300">•</span>
                    <span class="font-mono text-slate-400 text-[10px]">${escapeHtml(sub.pdf_filename)}</span>
                </span>
            </div>
        </td>
        <td class="py-3.5 px-4">
            ${statusBadge}
        </td>
        <td class="py-3.5 px-4 text-xs">
            ${compDisplay}
        </td>
        <td class="py-3.5 px-4 text-xs">
            ${novDisplay}
        </td>
        <td class="py-3.5 px-4">
            ${scoreDisplay}
        </td>
        <td class="py-3.5 px-4 text-[11px] text-slate-500 font-mono">
            ${sub.processing_time_seconds > 0 ? `${sub.processing_time_seconds}s` : '--'}
        </td>
        <td class="py-3.5 px-4 text-right">
            <button class="px-3 py-1.5 bg-white hover:bg-slate-100 text-slate-700 rounded-lg text-xs font-semibold transition border border-slate-200 shadow-sm" onclick="event.stopPropagation(); openReportModal(${sub.id})">
                View Dossier
            </button>
        </td>
    </tr>
    `;
}

function initDropzone() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('file-input');
    if (!dropzone || !fileInput) return;

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dropzone-active');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dropzone-active');
        }, false);
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files && files.length > 0) {
            handleUploadFiles(files);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleUploadFiles(e.target.files);
        }
    });
}

async function handleUploadFiles(files) {
    const formData = new FormData();
    let validCount = 0;

    for (let i = 0; i < files.length; i++) {
        if (files[i].name.toLowerCase().endsWith('.pdf')) {
            formData.append('files', files[i]);
            validCount++;
        }
    }

    if (validCount === 0) {
        showToast('Please select valid PDF documents.', 'error');
        return;
    }

    const uploadStatus = document.getElementById('upload-status');
    if (uploadStatus) {
        uploadStatus.classList.remove('hidden');
        uploadStatus.textContent = `Evaluating ${validCount} proposal(s) with Multi-Agent Pipeline...`;
    }

    try {
        const res = await fetch('/api/submissions/upload', {
            method: 'POST',
            body: formData
        });

        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.detail || 'Upload failed');
        }

        const data = await res.json();
        showToast(data.message, 'success');
        
        loadDashboardStats();
        loadSubmissions();
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        if (uploadStatus) {
            uploadStatus.classList.add('hidden');
        }
        document.getElementById('file-input').value = '';
    }
}

async function loadDemoSamples() {
    const btn = document.getElementById('btn-load-demo');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `
            <svg class="animate-spin -ml-0.5 mr-1 h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>Evaluating 3 Papers...</span>
        `;
    }

    try {
        const res = await fetch('/demo/load-samples', { method: 'POST' });
        const data = await res.json();
        showToast(data.message, 'success');
        loadDashboardStats();
        loadSubmissions();
    } catch (err) {
        showToast('Failed to load sample proposals', 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `
                <svg class="w-4 h-4 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
                </svg>
                <span>Load 3 Sample Papers</span>
            `;
        }
    }
}

async function openReportModal(id) {
    const modal = document.getElementById('report-modal');
    const modalContent = document.getElementById('modal-body-content');
    modal.classList.remove('hidden');

    modalContent.innerHTML = `
        <div class="py-16 text-center text-xs text-slate-500 flex flex-col items-center justify-center gap-2">
            <svg class="animate-spin h-6 w-6 text-slate-600" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>Loading evaluation dossier...</span>
        </div>
    `;

    try {
        const res = await fetch(`/api/submissions/${id}/report`);
        if (!res.ok) throw new Error('Could not retrieve evaluation report.');
        const data = await res.json();
        renderModalDetails(data);
    } catch (err) {
        modalContent.innerHTML = `<div class="p-6 text-center text-rose-600 text-xs font-semibold">${err.message}</div>`;
    }
}

function closeReportModal() {
    document.getElementById('report-modal').classList.add('hidden');
}

// Close on clicking backdrop
document.addEventListener('click', (e) => {
    const modal = document.getElementById('report-modal');
    if (e.target === modal) {
        closeReportModal();
    }
});

function renderModalDetails(sub) {
    const modalContent = document.getElementById('modal-body-content');

    let statusPill = '';
    if (sub.status === 'approved') {
        statusPill = `<span class="px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-sm">✓ Approved for Faculty</span>`;
    } else if (sub.status === 'revision') {
        statusPill = `<span class="px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200 shadow-sm">⚠ Needs Revision</span>`;
    } else if (sub.status === 'flagged') {
        statusPill = `<span class="px-3 py-1 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200 shadow-sm">✗ Flagged for Low Novelty</span>`;
    } else {
        statusPill = `<span class="px-3 py-1 rounded-full text-xs font-bold bg-slate-100 text-slate-700 border border-slate-200">Evaluating</span>`;
    }

    const allSections = ['Introduction', 'Methodology', 'Results', 'Conclusion'];
    const detected = sub.detected_sections || [];

    const sectionChecklist = allSections.map(sec => {
        const isPresent = detected.includes(sec);
        return `
            <div class="flex items-center justify-between p-2 rounded-md ${isPresent ? 'bg-emerald-50/50 border border-emerald-100' : 'bg-rose-50/50 border border-rose-100'} text-xs">
                <span class="font-medium ${isPresent ? 'text-slate-800' : 'text-rose-900'}">${sec}</span>
                <span class="${isPresent ? 'text-emerald-700 font-bold' : 'text-rose-600 font-bold'}">${isPresent ? '✓ Detected' : '✗ Missing'}</span>
            </div>
        `;
    }).join('');

    const matchesHtml = (sub.search_matches && sub.search_matches.length > 0)
        ? sub.search_matches.map(m => `
            <div class="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1.5 text-xs">
                <div class="flex items-center justify-between">
                    <span class="font-bold text-slate-900">${escapeHtml(m.title)}</span>
                    <span class="text-[10px] font-semibold px-2 py-0.5 rounded-full ${m.similarity_level === 'High' ? 'bg-rose-100 text-rose-800' : 'bg-slate-200 text-slate-700'}">${m.similarity_level} Overlap</span>
                </div>
                <p class="text-[11px] text-slate-600 leading-relaxed">${escapeHtml(m.snippet)}</p>
                <div class="text-[10px] text-slate-400 font-mono">${escapeHtml(m.source_type || 'Literature Index')}</div>
            </div>
        `).join('')
        : '<p class="text-[11px] text-slate-500 italic p-3 bg-slate-50 rounded-lg border border-slate-200">No duplicate or saturated literature matches detected.</p>';

    modalContent.innerHTML = `
        <div class="space-y-6">
            <!-- Modal Header -->
            <div class="flex items-start justify-between gap-4 border-b border-slate-200 pb-4">
                <div>
                    <div class="flex items-center gap-2 mb-2">
                        ${statusPill}
                        <span class="text-xs text-slate-400 font-mono">${sub.processing_time_seconds || 0}s pipeline latency</span>
                    </div>
                    <h2 class="text-xl font-bold text-slate-900 leading-snug">${escapeHtml(sub.title)}</h2>
                    <p class="text-xs text-slate-500 mt-1 flex items-center gap-2">
                        <span>Applicant: <strong class="text-slate-800">${escapeHtml(sub.student_name || 'Anonymous Applicant')}</strong></span>
                        <span>•</span>
                        <span class="font-mono text-slate-400">${escapeHtml(sub.pdf_filename)}</span>
                    </p>
                </div>
                <div class="text-right shrink-0 bg-slate-50 p-3 rounded-xl border border-slate-200">
                    <span class="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Final Score</span>
                    <span class="text-2xl font-black text-slate-900">${sub.overall_score ? sub.overall_score.toFixed(1) : '0.0'}<span class="text-xs text-slate-400 font-normal"> / 10</span></span>
                </div>
            </div>

            <!-- 3-Sentence Executive Review -->
            <div class="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
                <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Stage 3 Executive Review (3 Sentences)</span>
                <p class="text-xs text-slate-800 leading-relaxed font-medium">
                    "${escapeHtml(sub.summary || 'Summary pending.')}"
                </p>
            </div>

            <!-- 3-Stage Details Grid -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                
                <!-- Stage 1 -->
                <div class="p-4 rounded-xl bg-white border border-slate-200 space-y-2.5 shadow-sm">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-2">
                        <span class="text-[11px] font-bold text-slate-700 uppercase">Stage 1: Compliance</span>
                        <span class="text-xs font-bold text-slate-900">${sub.compliance_score.toFixed(1)} / 10</span>
                    </div>
                    <div class="text-[11px] text-slate-600">
                        Word Count: <strong class="text-slate-900">${sub.word_count}</strong> words <br>
                        <span class="text-slate-400">(Required: 250–500 words)</span>
                    </div>
                    <div class="space-y-1.5 pt-1">
                        ${sectionChecklist}
                    </div>
                    <p class="text-[10px] text-slate-500 leading-tight pt-1">${escapeHtml(sub.compliance_feedback || '')}</p>
                </div>

                <!-- Stage 2 -->
                <div class="p-4 rounded-xl bg-white border border-slate-200 space-y-2.5 shadow-sm">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-2">
                        <span class="text-[11px] font-bold text-slate-700 uppercase">Stage 2: Novelty</span>
                        <span class="text-xs font-bold text-slate-900">${sub.novelty_score.toFixed(1)} / 10</span>
                    </div>
                    <p class="text-xs font-semibold text-slate-800">${escapeHtml(sub.novelty_verdict || '')}</p>
                    <div class="space-y-1.5 pt-1 max-h-52 overflow-y-auto">
                        ${matchesHtml}
                    </div>
                </div>

                <!-- Stage 3 -->
                <div class="p-4 rounded-xl bg-white border border-slate-200 space-y-2.5 shadow-sm">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-2">
                        <span class="text-[11px] font-bold text-slate-700 uppercase">Stage 3: Critic</span>
                        <span class="text-xs font-bold text-slate-900">${sub.overall_score.toFixed(1)} / 10</span>
                    </div>
                    <div class="text-[11px] text-slate-600">
                        Dataset Feasibility: <strong class="text-slate-900">${sub.dataset_feasibility || 'Moderate'}</strong>
                    </div>
                    <p class="text-[11px] text-slate-600 leading-relaxed">${escapeHtml(sub.dataset_analysis || '')}</p>
                    <div class="pt-2 border-t border-slate-100 space-y-1 text-[11px] text-slate-600">
                        <div>Technical Depth: <strong class="text-slate-800">${sub.technical_depth_score || 0}/10</strong></div>
                        <div>Methodology Rigor: <strong class="text-slate-800">${sub.methodology_rigor_score || 0}/10</strong></div>
                    </div>
                </div>

            </div>

            <!-- Footer Actions -->
            <div class="flex items-center justify-between pt-4 border-t border-slate-200">
                <a href="/report/${sub.id}" target="_blank" class="px-3.5 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition border border-slate-200 flex items-center gap-1.5">
                    <svg class="w-4 h-4 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                    </svg>
                    <span>Open Printable Report</span>
                </a>
                <button onclick="closeReportModal()" class="px-5 py-2 bg-slate-900 text-white hover:bg-slate-800 rounded-lg text-xs font-semibold transition shadow-sm">
                    Close
                </button>
            </div>
        </div>
    `;
}

function startPolling() {
    if (pollingTimer) clearInterval(pollingTimer);
    pollingTimer = setInterval(async () => {
        const processingItems = document.querySelectorAll('.pulse-subtle');
        if (processingItems.length > 0) {
            loadDashboardStats();
            loadSubmissions();
        }
    }, 2500);
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = 'fixed bottom-5 right-5 px-4 py-3 rounded-lg text-xs font-semibold shadow-modal z-50 transition bg-slate-900 text-white flex items-center gap-2 border border-slate-800';
    toast.innerHTML = `
        <svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
        </svg>
        <span>${escapeHtml(message)}</span>
    `;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
