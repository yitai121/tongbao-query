/**
 * 通宝奖励查询系统 - 前端脚本
 */

// ========== 页面加载 ==========
document.addEventListener("DOMContentLoaded", () => {
    loadStats();
    // 回车查询
    document.getElementById("phoneInput").addEventListener("keydown", (e) => {
        if (e.key === "Enter") doQuery();
    });
    // 输入校验
    document.getElementById("phoneInput").addEventListener("input", (e) => {
        e.target.value = e.target.value.replace(/\D/g, "").slice(0, 11);
        updateHint(e.target.value);
    });
    // 定时刷新统计
    setInterval(loadStats, 60000);
});

// ========== 输入提示 ==========
function updateHint(val) {
    const hint = document.getElementById("inputHint");
    if (!val) {
        hint.textContent = "";
    } else if (val.length < 11) {
        hint.textContent = `还需输入 ${11 - val.length} 位`;
    } else if (val.length === 11) {
        hint.textContent = "✅ 手机号格式正确，点击查询";
        hint.style.color = "#10b981";
    }
}

// ========== 查询 ==========
async function doQuery() {
    const phone = document.getElementById("phoneInput").value.trim();

    if (!phone) {
        showError("请输入手机号");
        return;
    }
    if (!/^\d{11}$/.test(phone)) {
        showError("请输入正确的11位手机号");
        return;
    }

    // 显示加载
    hideAll();
    document.getElementById("loading").classList.remove("hidden");

    try {
        const resp = await fetch(`/api/query?phone=${phone}`);
        const json = await resp.json();

        document.getElementById("loading").classList.add("hidden");

        if (json.code === 200) {
            showResult(json.data);
        } else if (json.code === 404) {
            document.getElementById("emptyState").classList.remove("hidden");
        } else {
            showError(json.msg || "查询失败");
        }
    } catch (err) {
        document.getElementById("loading").classList.add("hidden");
        showError("网络错误，请稍后重试");
    }
}

// ========== 显示结果 ==========
function showResult(data) {
    const { phone, records, summary } = data;

    // 汇总
    document.getElementById("totalReward").textContent = formatNum(summary.total);
    document.getElementById("totalDays").textContent = summary.days;
    const avg = summary.days > 0 ? (summary.total / summary.days).toFixed(1) : 0;
    document.getElementById("avgReward").textContent = avg;

    // 手机号标签
    document.getElementById("phoneTag").textContent = maskPhone(phone);

    // 明细表格
    const tbody = document.getElementById("detailBody");
    tbody.innerHTML = "";
    records.forEach((r, i) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${i + 1}</td>
            <td>${r.record_date}</td>
            <td class="reward-value">+${formatNum(r.reward)}</td>
        `;
        tbody.appendChild(tr);
    });

    document.getElementById("resultArea").classList.remove("hidden");
}

// ========== 加载统计 ==========
async function loadStats() {
    try {
        const resp = await fetch("/api/stats");
        const json = await resp.json();
        if (json.code === 200) {
            document.getElementById("statUsers").textContent = json.data.users || 0;
            document.getElementById("statRecords").textContent = json.data.records || 0;
            const lastSync = json.data.last_sync;
            document.getElementById("statSync").textContent =
                lastSync ? formatTime(lastSync.sync_time) : "--";
        }
    } catch (e) {
        // 静默失败
    }
}

// ========== 工具函数 ==========
function hideAll() {
    document.getElementById("resultArea").classList.add("hidden");
    document.getElementById("emptyState").classList.add("hidden");
    document.getElementById("errorToast").classList.add("hidden");
}

function showError(msg) {
    const toast = document.getElementById("errorToast");
    document.getElementById("errorMsg").textContent = msg;
    toast.classList.remove("hidden");
    setTimeout(() => toast.classList.add("hidden"), 3000);
}

function formatNum(n) {
    const num = parseFloat(n) || 0;
    if (num >= 10000) return (num / 10000).toFixed(1) + "万";
    return num.toLocaleString("zh-CN", { maximumFractionDigits: 2 });
}

function maskPhone(phone) {
    return phone.slice(0, 3) + "****" + phone.slice(7);
}

function formatTime(t) {
    if (!t) return "--";
    const d = new Date(t);
    const now = new Date();
    const diff = now - d;
    if (diff < 60000) return "刚刚";
    if (diff < 3600000) return Math.floor(diff / 60000) + "分钟前";
    if (diff < 86400000) return Math.floor(diff / 3600000) + "小时前";
    return t.slice(5, 16);
}

// ========== 导入弹窗 ==========
let selectedFile = null;

function showImportModal() {
    document.getElementById("importModal").classList.remove("hidden");
    resetImportModal();
}

function hideImportModal() {
    document.getElementById("importModal").classList.add("hidden");
    resetImportModal();
}

function resetImportModal() {
    selectedFile = null;
    document.getElementById("fileInput").value = "";
    document.getElementById("fileInfo").classList.add("hidden");
    document.getElementById("importResult").classList.add("hidden");
    document.getElementById("importBtn").disabled = true;
    document.querySelector(".upload-content").style.display = "";
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    selectedFile = file;
    document.getElementById("fileName").textContent = file.name;
    document.getElementById("fileInfo").classList.remove("hidden");
    document.querySelector(".upload-content").style.display = "none";
    document.getElementById("importBtn").disabled = false;
    document.getElementById("importResult").classList.add("hidden");
}

function clearFile() {
    selectedFile = null;
    document.getElementById("fileInput").value = "";
    document.getElementById("fileInfo").classList.add("hidden");
    document.querySelector(".upload-content").style.display = "";
    document.getElementById("importBtn").disabled = true;
}

async function doImport() {
    if (!selectedFile) return;

    const btn = document.getElementById("importBtn");
    const resultDiv = document.getElementById("importResult");

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 导入中...';
    resultDiv.classList.add("hidden");

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
        const resp = await fetch("/api/import", {
            method: "POST",
            body: formData
        });
        const json = await resp.json();

        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-upload"></i> 开始导入';

        resultDiv.classList.remove("hidden");
        if (json.code === 200) {
            resultDiv.className = "import-result success";
            resultDiv.innerHTML = `<i class="fas fa-check-circle"></i> ${json.msg}`;
            if (json.data.errors && json.data.errors.length > 0) {
                resultDiv.innerHTML += `<br><small style="color:#f59e0b">跳过: ${json.data.errors.join("; ")}</small>`;
            }
            // 刷新统计
            loadStats();
            // 2秒后关闭弹窗
            setTimeout(() => hideImportModal(), 2000);
        } else {
            resultDiv.className = "import-result error";
            resultDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${json.msg}`;
        }
    } catch (err) {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-upload"></i> 开始导入';
        resultDiv.classList.remove("hidden");
        resultDiv.className = "import-result error";
        resultDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> 网络错误，请稍后重试`;
    }
}

// 拖拽上传
document.addEventListener("DOMContentLoaded", () => {
    const uploadArea = document.getElementById("uploadArea");
    if (uploadArea) {
        uploadArea.addEventListener("dragover", (e) => {
            e.preventDefault();
            uploadArea.classList.add("dragover");
        });
        uploadArea.addEventListener("dragleave", () => {
            uploadArea.classList.remove("dragover");
        });
        uploadArea.addEventListener("drop", (e) => {
            e.preventDefault();
            uploadArea.classList.remove("dragover");
            const file = e.dataTransfer.files[0];
            if (file) {
                document.getElementById("fileInput").files = e.dataTransfer.files;
                handleFileSelect({ target: { files: [file] } });
            }
        });
    }
});
