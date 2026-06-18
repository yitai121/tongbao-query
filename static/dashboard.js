/**
 * 数据分析看板 - 前端脚本
 */

let dailyTrendChart = null;
let distributionChart = null;

// 页面加载
document.addEventListener("DOMContentLoaded", () => {
    loadDashboardData();
    // 定时刷新（5分钟）
    setInterval(loadDashboardData, 300000);
});

// 加载看板数据
async function loadDashboardData() {
    try {
        const resp = await fetch("/api/dashboard");
        const json = await resp.json();

        if (json.code === 200) {
            renderOverview(json.data.overview);
            renderDailyTrend(json.data.daily_trend);
            renderDistribution(json.data.distribution);
            renderLeaderboard(json.data.leaderboard);
            document.getElementById("updateTime").textContent = formatTime(new Date());
        }
    } catch (err) {
        console.error("加载看板数据失败:", err);
    }
}

// 刷新数据
function refreshData() {
    const btn = document.querySelector(".btn-refresh");
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 刷新中...';
    btn.disabled = true;

    loadDashboardData().finally(() => {
        btn.innerHTML = '<i class="fas fa-sync-alt"></i> 刷新数据';
        btn.disabled = false;
    });
}

// 渲染概览
function renderOverview(data) {
    document.getElementById("totalUsers").textContent = data.total_users || 0;
    document.getElementById("totalRecords").textContent = data.total_records || 0;
    document.getElementById("totalReward").textContent = formatNum(data.total_reward);
    document.getElementById("avgReward").textContent = formatNum(data.avg_reward);
}

// 渲染每日趋势图
function renderDailyTrend(data) {
    const ctx = document.getElementById("dailyTrendChart").getContext("2d");

    if (dailyTrendChart) {
        dailyTrendChart.destroy();
    }

    const labels = data.map(d => d.record_date.slice(5)); // MM-DD
    const rewardData = data.map(d => d.daily_reward);
    const userCount = data.map(d => d.active_users);

    dailyTrendChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "每日奖励",
                    data: rewardData,
                    borderColor: "#f59e0b",
                    backgroundColor: "rgba(245, 158, 11, 0.1)",
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    yAxisID: "y"
                },
                {
                    label: "活跃用户",
                    data: userCount,
                    borderColor: "#6366f1",
                    backgroundColor: "rgba(99, 102, 241, 0.1)",
                    borderWidth: 2,
                    fill: false,
                    tension: 0.4,
                    yAxisID: "y1"
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: "index",
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: "top",
                    labels: {
                        color: "#94a3b8",
                        font: {
                            family: "Inter"
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: "rgba(255, 255, 255, 0.05)"
                    },
                    ticks: {
                        color: "#94a3b8",
                        font: {
                            family: "Inter"
                        }
                    }
                },
                y: {
                    type: "linear",
                    display: true,
                    position: "left",
                    grid: {
                        color: "rgba(255, 255, 255, 0.05)"
                    },
                    ticks: {
                        color: "#94a3b8",
                        font: {
                            family: "Inter"
                        }
                    }
                },
                y1: {
                    type: "linear",
                    display: true,
                    position: "right",
                    grid: {
                        drawOnChartArea: false
                    },
                    ticks: {
                        color: "#94a3b8",
                        font: {
                            family: "Inter"
                        }
                    }
                }
            }
        }
    });
}

// 渲染奖励分布图
function renderDistribution(data) {
    const ctx = document.getElementById("distributionChart").getContext("2d");

    if (distributionChart) {
        distributionChart.destroy();
    }

    const labels = data.map(d => d.reward_range);
    const counts = data.map(d => d.count);

    distributionChart = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: counts,
                backgroundColor: [
                    "#6366f1",
                    "#818cf8",
                    "#f59e0b",
                    "#fbbf24",
                    "#10b981"
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        color: "#94a3b8",
                        font: {
                            family: "Inter"
                        },
                        padding: 16
                    }
                }
            }
        }
    });
}

// 渲染排行榜
function renderLeaderboard(data) {
    const tbody = document.getElementById("leaderboardBody");
    tbody.innerHTML = "";

    data.forEach((item, index) => {
        const rank = index + 1;
        let rankClass = "";
        if (rank === 1) rankClass = "rank-1";
        else if (rank === 2) rankClass = "rank-2";
        else if (rank === 3) rankClass = "rank-3";

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td class="rank-cell ${rankClass}">${rank}</td>
            <td class="phone-cell">${maskPhone(item.phone)}</td>
            <td class="reward-cell">${formatNum(item.total_reward)}</td>
            <td>${item.record_days} 天</td>
            <td>${formatNum(item.avg_reward)}</td>
        `;
        tbody.appendChild(tr);
    });
}

// 工具函数
function formatNum(n) {
    const num = parseFloat(n) || 0;
    if (num >= 10000) return (num / 10000).toFixed(1) + "万";
    return num.toLocaleString("zh-CN", { maximumFractionDigits: 1 });
}

function maskPhone(phone) {
    return phone.slice(0, 3) + "****" + phone.slice(7);
}

function formatTime(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, "0");
    const d = String(date.getDate()).padStart(2, "0");
    const h = String(date.getHours()).padStart(2, "0");
    const min = String(date.getMinutes()).padStart(2, "0");
    return `${y}-${m}-${d} ${h}:${min}`;
}
