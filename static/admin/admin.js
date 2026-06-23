/**
 * 管理后台前端逻辑
 */

// ========== Tab 切换 ==========
document.querySelectorAll('.tab-btn[data-tab]').forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        const tab = item.dataset.tab;

        // 切换导航高亮
        document.querySelectorAll('.tab-btn[data-tab]').forEach(n => n.classList.remove('active'));
        item.classList.add('active');

        // 切换内容
        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
        document.getElementById('tab-' + tab).classList.add('active');

        // 加载对应数据
        if (tab === 'dashboard') loadDashboard();
        if (tab === 'sync') loadSyncLogs(1);
        if (tab === 'config') loadConfig();
        if (tab === 'pagination') loadPaginationConfig();
    });
});

// ========== 退出登录 ==========
document.getElementById('logoutBtn').addEventListener('click', async (e) => {
    e.preventDefault();
    await fetch('/api/admin/logout', { method: 'POST' });
    window.location.href = '/admin/login';
});

// ========== 数据看板 ==========
let dailyTrendChart = null;
let distributionChart = null;

async function loadDashboard() {
    try {
        const res = await fetch('/api/dashboard');
        const result = await res.json();
        if (result.code !== 200) return;

        const data = result.data;
        const overview = data.overview;

        document.getElementById('totalUsers').textContent = overview.total_users;
        document.getElementById('totalDays').textContent = overview.total_days;
        document.getElementById('totalReward').textContent = formatNumber(overview.total_reward);
        document.getElementById('dailyAvg').textContent = formatNumber(overview.daily_avg);

        // 每日趋势图
        renderDailyTrend(data.daily_trend);

        // 奖励分布图
        renderDistribution(data.distribution);

        // 排行榜
        renderLeaderboard(data.leaderboard);
    } catch (err) {
        console.error('加载看板数据失败:', err);
    }
}

function formatNumber(num) {
    if (num >= 10000) {
        return (num / 10000).toFixed(1) + '万';
    }
    return num.toFixed(2);
}

function renderDailyTrend(trend) {
    const ctx = document.getElementById('dailyTrendChart').getContext('2d');
    if (dailyTrendChart) dailyTrendChart.destroy();

    dailyTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: trend.map(d => d.record_date.slice(5)),
            datasets: [
                {
                    label: '奖励总额',
                    data: trend.map(d => d.daily_reward),
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    fill: true,
                    tension: 0.4
                },
                {
                    label: '活跃用户',
                    data: trend.map(d => d.active_users),
                    borderColor: '#764ba2',
                    backgroundColor: 'rgba(118, 75, 162, 0.1)',
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true, position: 'left' },
                y1: { beginAtZero: true, position: 'right', grid: { drawOnChartArea: false } }
            }
        }
    });
}

function renderDistribution(distribution) {
    const ctx = document.getElementById('distributionChart').getContext('2d');
    if (distributionChart) distributionChart.destroy();

    distributionChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: distribution.map(d => d.reward_range),
            datasets: [{
                data: distribution.map(d => d.count),
                backgroundColor: ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b']
            }]
        },
        options: { responsive: true }
    });
}

function renderLeaderboard(leaderboard) {
    const tbody = document.querySelector('#leaderboardTable tbody');
    tbody.innerHTML = leaderboard.map((item, i) => `
        <tr>
            <td>${i + 1}</td>
            <td>${maskPhone(item.phone)}</td>
            <td>${formatNumber(item.total_reward)}</td>
            <td>${item.record_days}</td>
            <td>${formatNumber(item.avg_reward)}</td>
        </tr>
    `).join('');
}

function maskPhone(phone) {
    if (!phone || phone.length < 7) return phone;
    return phone.slice(0, 3) + '****' + phone.slice(-4);
}

// ========== 同步控制 ==========
document.getElementById('syncBtn').addEventListener('click', async () => {
    const btn = document.getElementById('syncBtn');
    const resultDiv = document.getElementById('syncResult');

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 同步中...';
    resultDiv.style.display = 'none';

    try {
        const res = await fetch('/api/sync', { method: 'POST' });
        const result = await res.json();
        resultDiv.style.display = 'block';

        if (result.code === 200) {
            resultDiv.className = 'sync-result result-success';
            resultDiv.textContent = `同步成功！共同步 ${result.data.record_count} 条记录。`;
            loadSyncLogs(1);
        } else {
            resultDiv.className = 'sync-result result-error';
            resultDiv.textContent = `同步失败：${result.msg}`;
        }
    } catch (err) {
        resultDiv.style.display = 'block';
        resultDiv.className = 'sync-result result-error';
        resultDiv.textContent = '网络错误，请重试';
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-sync-alt"></i> 立即同步';
    }
});

let currentSyncPage = 1;

async function loadSyncLogs(page) {
    currentSyncPage = page;
    try {
        const res = await fetch(`/api/admin/sync/logs?page=${page}&per_page=10`);
        const result = await res.json();
        if (result.code !== 200) return;

        const logs = result.data.logs;
        const total = result.data.total;
        const totalPages = Math.ceil(total / 10);

        const tbody = document.querySelector('#syncLogTable tbody');
        tbody.innerHTML = logs.map(log => `
            <tr>
                <td>${log.sync_time}</td>
                <td><span class="status-badge ${log.status === 'success' ? 'status-success' : 'status-error'}">${log.status === 'success' ? '成功' : '失败'}</span></td>
                <td>${log.record_count}</td>
                <td>${log.message || '-'}</td>
            </tr>
        `).join('');

        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:#999">暂无同步记录</td></tr>';
        }

        // 分页
        const paginationDiv = document.getElementById('syncLogPagination');
        paginationDiv.innerHTML = `
            <button ${page <= 1 ? 'disabled' : ''} onclick="loadSyncLogs(${page - 1})">上一页</button>
            <span class="page-info">第 ${page} / ${totalPages || 1} 页，共 ${total} 条</span>
            <button ${page >= totalPages ? 'disabled' : ''} onclick="loadSyncLogs(${page + 1})">下一页</button>
        `;
    } catch (err) {
        console.error('加载同步日志失败:', err);
    }
}

// ========== 系统配置 ==========
async function loadConfig() {
    try {
        const res = await fetch('/api/admin/config');
        const result = await res.json();
        if (result.code !== 200) return;

        const configs = result.data;
        const configMap = {};
        configs.forEach(c => { configMap[c.key] = c.value; });

        document.getElementById('cfg_system_name').value = configMap['system_name'] || '';
        document.getElementById('cfg_doc_id').value = configMap['doc_id'] || '';
        document.getElementById('cfg_sheet_id').value = configMap['sheet_id'] || '';
        document.getElementById('cfg_phone_column').value = configMap['phone_column'] || '';
        document.getElementById('cfg_reward_column').value = configMap['reward_column'] || '';
        document.getElementById('cfg_sync_interval').value = configMap['sync_interval'] || '';
    } catch (err) {
        console.error('加载配置失败:', err);
    }
}

document.getElementById('configForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const configs = {
        system_name: document.getElementById('cfg_system_name').value,
        doc_id: document.getElementById('cfg_doc_id').value,
        sheet_id: document.getElementById('cfg_sheet_id').value,
        phone_column: document.getElementById('cfg_phone_column').value,
        reward_column: document.getElementById('cfg_reward_column').value,
        sync_interval: document.getElementById('cfg_sync_interval').value
    };

    try {
        const res = await fetch('/api/admin/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(configs)
        });
        const result = await res.json();
        const resultDiv = document.getElementById('configResult');
        resultDiv.style.display = 'block';

        if (result.code === 200) {
            resultDiv.className = 'save-result result-success';
            resultDiv.textContent = '配置保存成功！';
        } else {
            resultDiv.className = 'save-result result-error';
            resultDiv.textContent = `保存失败：${result.msg}`;
        }

        setTimeout(() => { resultDiv.style.display = 'none'; }, 3000);
    } catch (err) {
        console.error('保存配置失败:', err);
    }
});

// ========== 分页配置 ==========
async function loadPaginationConfig() {
    try {
        const res = await fetch('/api/admin/config');
        const result = await res.json();
        if (result.code !== 200) return;

        const configs = result.data;
        const configMap = {};
        configs.forEach(c => { configMap[c.key] = c.value; });

        document.getElementById('cfg_page_size').value = configMap['page_size'] || '20';
    } catch (err) {
        console.error('加载分页配置失败:', err);
    }
}

document.getElementById('paginationForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const pageSize = document.getElementById('cfg_page_size').value;

    try {
        const res = await fetch('/api/admin/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ page_size: pageSize })
        });
        const result = await res.json();
        const resultDiv = document.getElementById('paginationResult');
        resultDiv.style.display = 'block';

        if (result.code === 200) {
            resultDiv.className = 'save-result result-success';
            resultDiv.textContent = '分页配置保存成功！';
        } else {
            resultDiv.className = 'save-result result-error';
            resultDiv.textContent = `保存失败：${result.msg}`;
        }

        setTimeout(() => { resultDiv.style.display = 'none'; }, 3000);
    } catch (err) {
        console.error('保存分页配置失败:', err);
    }
});

// 初始加载看板数据
loadDashboard();
