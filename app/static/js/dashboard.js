// Academic-ScreenX Complete Inline Controller & Event Handlers

let allSubmissions = [];
let currentFilter = 'all';
let currentSearch = '';
let currentSort = 'date_desc';
let pollingTimer = null;

document.addEventListener('DOMContentLoaded', () => {
    initDashboard();
});

function initDashboard() {
    setupEventListeners();
    setupDropZone();
    loadDashboardStats();
    loadSubmissions();
    startPolling();
}

function setupEventListeners() {
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                currentSearch = e.target.value.trim();
                loadSubmissions();
            }, 300);
        });
    }

    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) {
        sortSelect.addEventListener('change', (e) => {
            currentSort = e.target.value;
            loadSubmissions();
        });
    }

    const fileInput = document.getElementById('file-input');
    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files.length > 0) {
                uploadFiles(Array.from(e.target.files));
            }
        });
    }
}

function setFilter(filter) {
    currentFilter = filter || 'all';
    const filterButtons = document.querySelectorAll('.filter-btn');
    filterButtons.forEach(btn => {
        const btnStatus = btn.dataset.status || btn.dataset.filter || 'all';
        if (btnStatus === currentFilter) {
            btn.className = 'filter-btn px-3 py-1.5 rounded-md font-semibold transition bg-white text-slate-900 shadow-sm';
        } else {
            btn.className = 'filter-btn px-3 py-1.5 rounded-md font-medium transition text-slate-600 hover:text-slate-900';
        }
    });
    loadSubmissions();
}

async function loadDemoSamples() {
    const btn = document.getElementById('btn-load-demo');
    let originalHtml = '';
    if (btn) {
        originalHtml = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = `
            <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>Loading 3 Papers...</span>
        `;
    }

    try {
        const res = await fetch('/demo/load-samples', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin'
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || 'Failed to load sample papers.');
        }

        const data = await res.json();
        showToast(data.message || 'Queued 3 sample papers for evaluation.', 'success');
        
        await loadDashboardStats();
        await loadSubmissions();
    } catch (err) {
        showToast(err.message || 'Error loading sample papers.', 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }
    }
}

function setupDropZone() {
    const dropZone = document.getElementById('dropzone') || document.getElementById('drop-zone');
    if (!dropZone) return;

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add('border-slate-800', 'bg-slate-100');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('border-slate-800', 'bg-slate-100');
        }, false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = Array.from(dt.files).filter(f => f.name.toLowerCase().endsWith('.pdf') || f.name.toLowerCase().endsWith('.txt') || f.name.toLowerCase().endsWith('.md'));
        if (files.length > 0) {
            uploadFiles(files);
        } else {
            showToast('Please upload PDF, TXT, or MD proposal files.', 'warning');
        }
    }, false);
}

async function uploadFiles(files) {
    const validFiles = files.filter(f => f.name.toLowerCase().endsWith('.pdf') || f.name.toLowerCase().endsWith('.txt') || f.name.toLowerCase().endsWith('.md'));
    if (validFiles.length === 0) {
        showToast('Please select valid PDF or TXT files.', 'warning');
        return;
    }

    const formData = new FormData();
    validFiles.forEach(file => {
        formData.append('files', file);
    });

    const statusEl = document.getElementById('upload-status');
    if (statusEl) statusEl.classList.remove('hidden');

    try {
        const response = await fetch('/api/submissions/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'Upload failed');
        }

        const result = await response.json();
        showToast(result.message || 'Upload accepted.', 'success');
        
        const fileInput = document.getElementById('file-input');
        if (fileInput) fileInput.value = '';

        await loadDashboardStats();
        await loadSubmissions();
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        if (statusEl) statusEl.classList.add('hidden');
    }
}

async function loadDashboardStats() {
    try {
        const res = await fetch('/api/submissions/stats');
        if (!res.ok) return;
        const stats = await res.json();

        if (document.getElementById('stat-total')) {
            document.getElementById('stat-total').textContent = stats.total_uploaded;
        }
        if (document.getElementById('stat-approved-pct')) {
            document.getElementById('stat-approved-pct').textContent = `${stats.approved_pct}%`;
        }
        if (document.getElementById('stat-approved-count')) {
            document.getElementById('stat-approved-count').textContent = `(${stats.approved_count} papers)`;
        }
        if (document.getElementById('stat-revision-count')) {
            document.getElementById('stat-revision-count').textContent = stats.revision_count;
        }
        if (document.getElementById('stat-flagged-pct')) {
            document.getElementById('stat-flagged-pct').textContent = `${stats.flagged_pct}%`;
        }
        if (document.getElementById('stat-flagged-count')) {
            document.getElementById('stat-flagged-count').textContent = `(${stats.flagged_count} papers)`;
        }
        if (document.getElementById('stat-avg-time')) {
            document.getElementById('stat-avg-time').textContent = `${stats.avg_processing_time}s`;
        }
    } catch (e) {
        console.error('Failed to load stats', e);
    }
}

async function loadSubmissions() {
    const tableBody = document.getElementById('submissions-table-body');
    const emptyState = document.getElementById('empty-state');
    if (!tableBody) return;
    
    try {
        let url = `/api/submissions/list?sort=${currentSort}`;
        if (currentFilter !== 'all') {
            url += `&status=${currentFilter}`;
        }
        if (currentSearch) {
            url += `&q=${encodeURIComponent(currentSearch)}`;
        }

        const res = await fetch(url);
        if (!res.ok) throw new Error('Failed to fetch submissions');
        const data = await res.json();
        allSubmissions = data;

        if (data.length === 0) {
            tableBody.innerHTML = '';
            if (emptyState) emptyState.classList.remove('hidden');
            return;
        }

        if (emptyState) emptyState.classList.add('hidden');
        renderSubmissionsTable(data);
    } catch (e) {
        console.error('Error loading submissions', e);
    }
}

function renderSubmissionRowHtml(sub) {
    let statusBadge = '';
    if (sub.status === 'approved') {
        statusBadge = `<span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-sm">✓ Approved</span>`;
    } else if (sub.status === 'revision') {
        statusBadge = `<span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-50 text-amber-700 border border-amber-200 shadow-sm">⚠ Needs Revision</span>`;
    } else if (sub.status === 'flagged') {
        statusBadge = `<span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-50 text-rose-700 border border-rose-200 shadow-sm">✗ Flagged Novelty</span>`;
    } else if (sub.status === 'processing') {
        statusBadge = `<span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-50 text-blue-700 border border-blue-200 shadow-sm flex items-center gap-1.5"><span class="w-1.5 h-1.5 rounded-full bg-blue-500 animate-ping"></span> Processing</span>`;
    } else {
        statusBadge = `<span class="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-600 border border-slate-200">Queued</span>`;
    }

    const dateStr = new Date(sub.uploaded_at).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });

    let ragTag = '';
    if (sub.rag_match_status === 'PASS') {
        ragTag = `<span class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-blue-50 text-blue-700 border border-blue-200" title="RAG Criteria Met">RAG Match</span>`;
    } else if (sub.rag_match_status === 'FAIL') {
        ragTag = `<span class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-50 text-amber-700 border border-amber-200" title="RAG Missing Requirements">RAG Gaps</span>`;
    }

    return `
        <td class="px-4 py-3.5">
            <div class="flex items-start gap-3">
                <div class="w-8 h-8 rounded-lg bg-slate-100 border border-slate-200 flex items-center justify-center shrink-0 text-slate-600 font-bold text-xs mt-0.5 shadow-sm">
                    PDF
                </div>
                <div class="min-w-0 flex-1 space-y-0.5">
                    <div class="flex items-center gap-2 flex-wrap">
                        <button onclick="openReportModal(${sub.id})" class="text-xs font-bold text-slate-900 hover:text-blue-600 truncate text-left transition">
                            ${escapeHtml(sub.title || sub.pdf_filename)}
                        </button>
                        ${ragTag}
                    </div>
                    <div class="flex items-center gap-2 text-[10px] text-slate-500 flex-wrap">
                        <span>${escapeHtml(sub.student_name || 'Student Researcher')}</span>
                        <span>•</span>
                        <span>${sub.file_size_kb || 0} KB</span>
                        <span>•</span>
                        <span>${dateStr}</span>
                    </div>
                </div>
            </div>
        </td>
        <td class="px-4 py-3.5 whitespace-nowrap">
            ${statusBadge}
        </td>
        <td class="px-4 py-3.5 whitespace-nowrap">
            <div class="text-xs font-bold ${sub.compliance_score >= 8 ? 'text-emerald-700' : sub.compliance_score >= 5 ? 'text-amber-700' : 'text-slate-500'}">
                ${sub.compliance_score > 0 ? sub.compliance_score.toFixed(1) + ' / 10' : '—'}
            </div>
            <div class="text-[10px] text-slate-500">${sub.word_count || 0} words</div>
        </td>
        <td class="px-4 py-3.5 whitespace-nowrap">
            <div class="text-xs font-bold ${sub.novelty_score >= 7 ? 'text-emerald-700' : sub.novelty_score >= 4 ? 'text-amber-700' : 'text-rose-700'}">
                ${sub.novelty_score > 0 ? sub.novelty_score.toFixed(1) + ' / 10' : '—'}
            </div>
            <div class="text-[10px] text-slate-500 truncate max-w-[120px]">${escapeHtml(sub.novelty_verdict || 'Assessing...')}</div>
        </td>
        <td class="px-4 py-3.5 whitespace-nowrap">
            <div class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-lg ${sub.overall_score >= 7 ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : sub.overall_score >= 4 ? 'bg-amber-50 text-amber-800 border border-amber-200' : 'bg-slate-100 text-slate-700'} font-bold text-xs shadow-sm">
                <span>${sub.overall_score > 0 ? sub.overall_score.toFixed(1) : '—'}</span>
                <span class="text-[10px] font-normal opacity-70">/ 10</span>
            </div>
        </td>
        <td class="px-4 py-3.5 whitespace-nowrap text-xs text-slate-500 font-mono">
            ${sub.processing_time_seconds ? sub.processing_time_seconds.toFixed(2) + 's' : '—'}
        </td>
        <td class="px-4 py-3.5 whitespace-nowrap text-right text-xs">
            <div class="flex items-center justify-end gap-1.5">
                <button onclick="openReportModal(${sub.id})" class="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium transition border border-slate-200 text-[11px]">
                    Dossier
                </button>
                <button onclick="deleteSubmission(${sub.id})" class="p-1 rounded text-slate-400 hover:text-rose-600 transition" title="Delete submission">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                    </svg>
                </button>
            </div>
        </td>
    `;
}

function renderSubmissionsTable(submissions) {
    const tableBody = document.getElementById('submissions-table-body');
    const emptyState = document.getElementById('empty-state');
    if (!tableBody) return;

    if (!submissions || submissions.length === 0) {
        tableBody.innerHTML = '';
        if (emptyState) emptyState.classList.remove('hidden');
        return;
    }

    if (emptyState) emptyState.classList.add('hidden');

    const newIdSet = new Set(submissions.map(s => String(s.id)));
    
    // Remove deleted rows smoothly
    const existingRows = Array.from(tableBody.querySelectorAll('tr[id^="sub-row-"]'));
    existingRows.forEach(row => {
        const rowId = row.id.replace('sub-row-', '');
        if (!newIdSet.has(rowId)) {
            row.remove();
        }
    });

    // Reconcile and update existing rows or append new rows
    submissions.forEach((sub, index) => {
        const rowId = `sub-row-${sub.id}`;
        let row = document.getElementById(rowId);
        const isProcessing = sub.status === 'processing' || sub.status === 'pending';
        const signature = `${sub.status}_${sub.overall_score}_${sub.compliance_score}_${sub.novelty_score}_${sub.rag_match_status}_${sub.title}`;

        if (!row) {
            row = document.createElement('tr');
            row.id = rowId;
            row.className = `hover:bg-slate-50/80 transition group ${isProcessing ? 'pulse-subtle' : ''}`;
            row.dataset.signature = signature;
            row.innerHTML = renderSubmissionRowHtml(sub);

            const currentChildren = tableBody.children;
            if (index < currentChildren.length) {
                tableBody.insertBefore(row, currentChildren[index]);
            } else {
                tableBody.appendChild(row);
            }
        } else {
            if (row.dataset.signature !== signature) {
                row.dataset.signature = signature;
                row.className = `hover:bg-slate-50/80 transition group ${isProcessing ? 'pulse-subtle' : ''}`;
                row.innerHTML = renderSubmissionRowHtml(sub);
            }
            const currentChildren = tableBody.children;
            if (currentChildren[index] !== row) {
                tableBody.insertBefore(row, currentChildren[index] || null);
            }
        }
    });
}

async function openReportModal(id) {
    const modal = document.getElementById('report-modal');
    const modalContent = document.getElementById('modal-body-content');
    if (!modal || !modalContent) return;

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
    const modal = document.getElementById('report-modal');
    if (modal) modal.classList.add('hidden');
}

document.addEventListener('click', (e) => {
    const modal = document.getElementById('report-modal');
    if (e.target === modal) {
        closeReportModal();
    }
});

function renderModalDetails(sub) {
    const modalContent = document.getElementById('modal-body-content');
    if (!modalContent) return;

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

    const ragEvidenceList = (sub.rag_evidence && sub.rag_evidence.length > 0)
        ? sub.rag_evidence.map(e => `<li>${escapeHtml(e)}</li>`).join('')
        : '<li class="italic text-slate-400">Baseline research proposal content extracted.</li>';

    const ragMissingList = (sub.rag_missing_requirements && sub.rag_missing_requirements.length > 0)
        ? sub.rag_missing_requirements.map(m => `<li>${escapeHtml(m)}</li>`).join('')
        : '<li class="text-emerald-700 font-semibold">None. All criteria satisfied.</li>';

    const ragStatusBadge = sub.rag_match_status === 'Qualified'
        ? `<span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-800">Qualified</span>`
        : sub.rag_match_status === 'Needs Review'
        ? `<span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800">Needs Review</span>`
        : `<span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-100 text-rose-800">Not Qualified</span>`;

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

            <!-- AI RAG Evaluation Layer Breakdown -->
            <div class="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                <div class="flex items-center justify-between border-b border-slate-200 pb-2">
                    <div class="flex items-center gap-2">
                        <span class="px-2 py-0.5 rounded bg-blue-600 text-white text-[10px] font-bold uppercase tracking-wider">RAG Layer</span>
                        <span class="font-bold text-slate-900 text-xs">Vector Retrieval & Criteria Evaluation</span>
                    </div>
                    ${ragStatusBadge}
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    <div class="p-3 bg-white rounded-lg border border-slate-200 space-y-1.5 shadow-sm">
                        <span class="text-[10px] font-bold text-emerald-800 uppercase block">✓ Key Evidence Found</span>
                        <ul class="text-[11px] text-slate-600 space-y-1 list-disc pl-4">
                            ${ragEvidenceList}
                        </ul>
                    </div>
                    <div class="p-3 bg-white rounded-lg border border-slate-200 space-y-1.5 shadow-sm">
                        <span class="text-[10px] font-bold text-amber-800 uppercase block">⚠ Missing Requirements / Gaps</span>
                        <ul class="text-[11px] text-slate-600 space-y-1 list-disc pl-4">
                            ${ragMissingList}
                        </ul>
                    </div>
                </div>
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

async function deleteSubmission(id) {
    if (!confirm('Are you sure you want to delete this submission record?')) return;
    try {
        const res = await fetch(`/api/submissions/${id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Could not delete submission.');
        showToast('Submission deleted successfully.', 'success');
        loadDashboardStats();
        loadSubmissions();
    } catch (e) {
        showToast(e.message, 'error');
    }
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    const bgClass = type === 'success' ? 'bg-emerald-800 text-white' : type === 'error' ? 'bg-rose-800 text-white' : 'bg-slate-900 text-white';
    
    toast.className = `px-4 py-3 rounded-xl text-xs font-medium shadow-lg transition-all transform duration-300 translate-y-2 opacity-0 flex items-center gap-2 ${bgClass}`;
    toast.innerHTML = `<span>${escapeHtml(message)}</span>`;
    
    container.appendChild(toast);
    setTimeout(() => {
        toast.classList.remove('translate-y-2', 'opacity-0');
    }, 10);

    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => toast.remove(), 300);
    }, 3500);
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