// Tab Logic
function openTab(evt, tabName) {
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tab-content");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("tab-btn");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";

    if (tabName === 'KnowledgeBase') {
        loadKB(1);
        loadStats();
    }
}

async function loadStats() {
    try {
        const res = await fetch('/issues/stats');
        const data = await res.json();

        document.getElementById('totalIssues').textContent = data.total.toLocaleString();

        const typeList = document.getElementById('topIssueTypes');
        typeList.innerHTML = Object.entries(data.by_type).map(([key, val]) =>
            `<li><span>${key}</span> <span>${val}</span></li>`
        ).join('');

        const priorityList = document.getElementById('topPriorities');
        priorityList.innerHTML = Object.entries(data.by_priority).map(([key, val]) =>
            `<li><span>${key}</span> <span>${val}</span></li>`
        ).join('');

    } catch (error) {
        console.error("Failed to load stats:", error);
    }
}

// Simulation Logic
document.getElementById('loadTestBtn').addEventListener('click', async () => {
    try {
        const res = await fetch('/simulation/test-data');
        const data = await res.json();

        if (data.error) {
            alert("Error loading test data: " + data.error);
            return;
        }

        document.getElementById('summary').value = data.summary;
        document.getElementById('description').value = data.description;
        // Optional: Fill region if available or leave blank

        // Auto-scroll to analyze button
        document.getElementById('analyzeBtn').scrollIntoView({ behavior: "smooth" });

    } catch (error) {
        console.error("Failed to load test data:", error);
    }
});

// Knowledge Base Logic
let currentPage = 1;
const limit = 15;

async function loadKB(page) {
    currentPage = page;
    const offset = (page - 1) * limit;
    const search = document.getElementById('kbSearch').value;

    let url = `/issues?limit=${limit}&offset=${offset}`;
    if (search) {
        url += `&search=${encodeURIComponent(search)}`;
    }

    try {
        const res = await fetch(url);
        const issues = await res.json();
        renderKB(issues);
        document.getElementById('pageInfo').textContent = `Page ${currentPage}`;
        document.getElementById('prevPage').disabled = currentPage === 1;
    } catch (error) {
        console.error("Failed to load KB:", error);
    }
}

function renderKB(issues) {
    const tbody = document.querySelector('#kbTable tbody');
    tbody.innerHTML = issues.map((issue, index) => `
        <tr onclick="openKBDetails(${index})" style="cursor: pointer;">
            <td><span style="color: #0052CC; font-weight: bold;">${issue.issue_key}</span></td>
            <td>${issue.summary}</td>
            <td>${issue.project_name || '-'}</td>
            <td><span class="tag medium">${issue.issue_type}</span></td>
            <td>${issue.priority}</td>
            <td><span class="tag low">${issue.status}</span></td>
        </tr>
    `).join('');

    // Store globally for detail view
    window.kbIssues = issues;
}

window.openKBDetails = function (index) {
    const data = window.kbIssues[index];
    openModal(data);
}

function changePage(delta) {
    const newPage = currentPage + delta;
    if (newPage < 1) return;
    loadKB(newPage);
}

let searchTimeout;
function searchKB() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        loadKB(1);
    }, 500);
}

// Existing Analyze Logic
document.getElementById('analyzeBtn').addEventListener('click', async () => {
    const summary = document.getElementById('summary').value;
    const description = document.getElementById('description').value;
    const region = document.getElementById('region').value;

    if (!summary) {
        alert("이슈 제목을 입력해주세요.");
        return;
    }

    const btn = document.getElementById('analyzeBtn');
    btn.disabled = true;
    btn.textContent = "분석 중입니다...";

    const payload = {
        summary: summary,
        description: description,
        custom_fields: region ? { "Region": region } : {}
    };

    try {
        // 1. Analyze
        const analyzeRes = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const analysis = await analyzeRes.json();
        renderAnalysis(analysis);
        renderComparison(description, analysis.translated_description);

        // 2. Route
        const routeRes = await fetch('/route', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const routing = await routeRes.json();
        renderRouting(routing);

        // 3. Search
        const searchRes = await fetch('/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: summary, limit: 3 })
        });
        const searchResults = await searchRes.json();
        renderSearch(searchResults);

    } catch (error) {
        console.error("Error:", error);
        alert("오류가 발생했습니다. 콘솔을 확인해주세요.");
    } finally {
        btn.disabled = false;
        btn.textContent = "분석 및 라우팅 시작";
    }
});

function renderAnalysis(data) {
    const container = document.getElementById('analysisResult');
    const urgencyClass = data.urgency.toLowerCase();

    container.innerHTML = `
        <div class="result-item"><span class="label">카테고리:</span> ${data.category}</div>
        <div class="result-item"><span class="label">긴급도:</span> <span class="tag ${urgencyClass}">${data.urgency}</span></div>
        <div class="result-item"><span class="label">국가/사이트:</span> ${data.country || '-'} / ${data.related_site || '-'}</div>
        <div class="result-item"><span class="label">원인 추정:</span> ${data.root_cause_hypothesis}</div>
        <div class="result-item"><span class="label">필요 조치:</span> ${data.required_action}</div>
        <div class="result-item"><span class="label">신뢰도:</span> ${(data.confidence_score * 100).toFixed(0)}%</div>
    `;
}

function renderComparison(original, translated) {
    document.getElementById('originalDesc').textContent = original || "내용 없음";
    document.getElementById('translatedDesc').textContent = translated || "번역 없음";
}

function renderRouting(data) {
    const container = document.getElementById('routingResult');
    container.innerHTML = `
        <div class="result-item" style="font-size: 1.2em; font-weight: bold; color: #0052CC;">
            ${data.recommended_team}
        </div>
        <div class="result-item"><span class="label">추천 사유:</span> ${data.reason}</div>
    `;
}

// Modal Logic
const modal = document.getElementById("detailsModal");
const span = document.getElementsByClassName("close-btn")[0];
let currentModalSummary = "";
let currentModalDescription = "";

span.onclick = function () {
    modal.style.display = "none";
}

window.onclick = function (event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
}

document.getElementById('modalTranslateBtn').addEventListener('click', async () => {
    const btn = document.getElementById('modalTranslateBtn');
    const container = document.getElementById('modalTranslatedDesc');

    btn.disabled = true;
    btn.textContent = "번역 중...";

    try {
        const analyzeRes = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ summary: currentModalSummary, description: currentModalDescription })
        });
        const analysis = await analyzeRes.json();
        container.textContent = analysis.translated_description;
    } catch (error) {
        console.error("Translation failed:", error);
        container.textContent = "번역 실패";
    }
});

function openModal(caseData) {
    currentModalSummary = caseData.summary;
    currentModalDescription = caseData.description;

    document.getElementById('modalTitle').textContent = `[${caseData.issue_key}] ${caseData.summary}`;
    document.getElementById('modalOriginalDesc').textContent = caseData.description || "내용 없음";

    // Reset translation area
    const transContainer = document.getElementById('modalTranslatedDesc');
    transContainer.innerHTML = '';
    const translateBtn = document.createElement('button');
    translateBtn.id = 'modalTranslateBtn'; // Re-create because we wiped innerHTML
    translateBtn.className = 'btn primary small';
    translateBtn.textContent = "번역하기 (Translate)";
    // Re-attach listener (or better, don't wipe button but just text)
    // Simpler: Just render the button again with onclick
    translateBtn.onclick = async () => {
        translateBtn.disabled = true;
        translateBtn.textContent = "번역 중...";
        try {
            const analyzeRes = await fetch('/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ summary: caseData.summary, description: caseData.description })
            });
            const analysis = await analyzeRes.json();
            transContainer.textContent = analysis.translated_description;
        } catch (error) {
            console.error(error);
            transContainer.textContent = "번역 실패";
        }
    };
    transContainer.appendChild(translateBtn);

    modal.style.display = "block";
}

function renderSearch(results) {
    const container = document.getElementById('searchResult');
    if (results.length === 0) {
        container.innerHTML = '<p class="placeholder">유사한 사례가 없습니다.</p>';
        return;
    }

    container.innerHTML = results.map((res, index) => `
        <div class="search-item" onclick="openDetails(${index})" style="cursor: pointer; hover: background-color: #f0f0f0;">
            <div style="font-weight: 600;">[${res.issue_key}] ${res.summary}</div>
            <div style="font-size: 0.9em; color: #42526E;">${res.status}</div>
            <div class="similarity">유사도: ${(res.similarity * 100).toFixed(1)}%</div>
        </div>
    `).join('');

    // Store results globally to access in openDetails
    window.searchResults = results;
}

window.openDetails = function (index) {
    const data = window.searchResults[index];
    openModal(data);
}
