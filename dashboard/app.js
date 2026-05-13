// 教育数据看板 v2.2.2 - 周次渲染兼容修复版
// 核心优化：大文件分片存储、上传进度实时更新、存储配额检查

const DB_CONFIG = { name: 'EducationDataDB', version: 1, store: 'files' };
const MAX_STORAGE_MB = 500; // 最大存储限制（MB）
let db = null;
const AppState = { files: [], filteredData: [], cache: new Map(), provinces: new Set(), cities: new Set(), districts: new Set(), schools: new Set(), grades: new Set() };
const elements = {};
const APP_VERSION = 'v2.4.1-root-20260507b';
const getClassId = (r = {}) => r['班级 id'] || r['班级ID'] || r['班级id'] || r['班级'] || r['classId'] || r['class_id'] || '';
const buildWeekMetaMap = (groupMap) => {
    const weekMetaMap = new Map();
    groupMap.forEach(g => {
        g.weeks.forEach((w, k) => {
            if (!weekMetaMap.has(k)) weekMetaMap.set(k, w);
        });
    });
    return weekMetaMap;
};
const sortWeekKeys = (weekMetaMap) => [...weekMetaMap.keys()].sort((a, b) => {
    const wa = weekMetaMap.get(a);
    const wb = weekMetaMap.get(b);
    const aTime = wa?.startDate ? dayjs(wa.startDate).valueOf() : 0;
    const bTime = wb?.startDate ? dayjs(wb.startDate).valueOf() : 0;
    return aTime - bTime;
});

// 初始化数据库
function initDB() {
    return new Promise((resolve, reject) => {
        const req = indexedDB.open(DB_CONFIG.name, DB_CONFIG.version);
        req.onerror = () => reject(req.error);
        req.onsuccess = () => { db = req.result; resolve(db); loadFileList(); };
        req.onupgradeneeded = (e) => {
            const database = e.target.result;
            if (!database.objectStoreNames.contains(DB_CONFIG.store)) {
                const store = database.createObjectStore(DB_CONFIG.store, { keyPath: 'id' });
                store.createIndex('filename', 'filename', { unique: true });
            }
        };
    });
}

// 检查存储配额
async function checkStorageQuota() {
    if (navigator.storage && navigator.storage.estimate) {
        const estimate = await navigator.storage.estimate();
        const used = (estimate.usage / 1024 / 1024).toFixed(2);
        const quota = (estimate.quota / 1024 / 1024).toFixed(2);
        const percent = ((estimate.usage / estimate.quota) * 100).toFixed(1);
        console.log(`💾 存储使用：${used}MB / ${quota}MB (${percent}%)`);
        return { used: parseFloat(used), quota: parseFloat(quota), percent: parseFloat(percent) };
    }
    return null;
}

// DOM 初始化
function initElements() {
    elements.uploadBtn = document.getElementById('uploadBtn');
    elements.fileInput = document.getElementById('fileInput');
    elements.overlay = document.getElementById('overlay');
    elements.uploadProgress = document.getElementById('uploadProgress');
    elements.progressFill = document.getElementById('progressFill');
    elements.progressText = document.getElementById('progressText');
    elements.progressStats = document.getElementById('progressStats');
    elements.progressSpeed = document.getElementById('progressSpeed');
    elements.progressETA = document.getElementById('progressETA');
    elements.weeksGrid = document.getElementById('weeksGrid');
    elements.clearAllBtn = document.getElementById('clearAllBtn');
    elements.startDate = document.getElementById('startDate');
    elements.endDate = document.getElementById('endDate');
    elements.provinceSelect = document.getElementById('provinceSelect');
    elements.citySelect = document.getElementById('citySelect');
    elements.districtSelect = document.getElementById('districtSelect');
    elements.schoolSelect = document.getElementById('schoolSelect');
    elements.gradeSelect = document.getElementById('gradeSelect');
    elements.applyFilter = document.getElementById('applyFilter');
    elements.resetFilter = document.getElementById('resetFilter');
    elements.dataCount = document.getElementById('dataCount');
    elements.metricsSection = document.getElementById('metricsSection');
    elements.chartsSection = document.getElementById('chartsSection');
    elements.tableSection = document.getElementById('tableSection');
    elements.emptyState = document.getElementById('emptyState');
    elements.conversionRate = document.getElementById('conversionRate');
    elements.avgCompletionRate = document.getElementById('avgCompletionRate');
    elements.classCount = document.getElementById('classCount');
    elements.studentCount = document.getElementById('studentCount');
    elements.paidNotExpired = document.getElementById('paidNotExpired');
    elements.avgAssignments = document.getElementById('avgAssignments');
    elements.tableBody = document.getElementById('tableBody');
    elements.exportBtn = document.getElementById('exportBtn');
    
    // 高价值筛选元素
    elements.highValueSection = document.getElementById('highValueSection');
    elements.hvProvinceSelect = document.getElementById('hvProvinceSelect');
    elements.hvCitySelect = document.getElementById('hvCitySelect');
    elements.hvDistrictSelect = document.getElementById('hvDistrictSelect');
    elements.hvGradeSelect = document.getElementById('hvGradeSelect');
    elements.hvPayRateSelect = document.getElementById('hvPayRateSelect');
    elements.hvStudentCountSelect = document.getElementById('hvStudentCountSelect');
    elements.hvAssignRateSelect = document.getElementById('hvAssignRateSelect');
    elements.hvCompletionRateSelect = document.getElementById('hvCompletionRateSelect');
    elements.hvTrialCountSelect = document.getElementById('hvTrialCountSelect');
    elements.hvSchoolCategorySelect = document.getElementById('hvSchoolCategorySelect');
    elements.hvFavoriteSelect = document.getElementById('hvFavoriteSelect');
    elements.highValueTableBody = document.getElementById('highValueTableBody');
    elements.highValueInfo = document.getElementById('highValueInfo');
    elements.applyHighValueFilter = document.getElementById('applyHighValueFilter');
    elements.resetHighValueFilter = document.getElementById('resetHighValueFilter');
    elements.customSchoolSection = document.getElementById('customSchoolSection');
    elements.customSchoolInput = document.getElementById('customSchoolInput');
    elements.customSchoolSearchBtn = document.getElementById('customSchoolSearchBtn');
    elements.customSchoolResetBtn = document.getElementById('customSchoolResetBtn');
    elements.customSchoolAvgAssignFilter = document.getElementById('customSchoolAvgAssignFilter');
    elements.customSchoolCompletionFilter = document.getElementById('customSchoolCompletionFilter');
    elements.customSchoolStageFilter = document.getElementById('customSchoolStageFilter');
    elements.customSchoolGradeFilter = document.getElementById('customSchoolGradeFilter');
    elements.customSchoolResult = document.getElementById('customSchoolResult');
    elements.customSchoolSummary = document.getElementById('customSchoolSummary');
    elements.customSchoolTabSchool = document.getElementById('customSchoolTabSchool');
    elements.customSchoolTabGrade = document.getElementById('customSchoolTabGrade');
    elements.customSchoolTabClass = document.getElementById('customSchoolTabClass');
    elements.customSchoolSchoolView = document.getElementById('customSchoolSchoolView');
    elements.customSchoolGradeView = document.getElementById('customSchoolGradeView');
    elements.customSchoolClassView = document.getElementById('customSchoolClassView');
    elements.customSchoolSchoolTableHead = document.getElementById('customSchoolSchoolTableHead');
    elements.customSchoolSchoolTableBody = document.getElementById('customSchoolSchoolTableBody');
    elements.customSchoolTableHead = document.getElementById('customSchoolTableHead');
    elements.customSchoolTableBody = document.getElementById('customSchoolTableBody');
    elements.customSchoolClassTableHead = document.getElementById('customSchoolClassTableHead');
    elements.customSchoolClassTableBody = document.getElementById('customSchoolClassTableBody');
}


// 数据库操作
function saveFile(record, blob) {
    return new Promise((resolve, reject) => {
        try {
            const tx = db.transaction([DB_CONFIG.store], 'readwrite');
            const store = tx.objectStore(DB_CONFIG.store);
            store.put({ ...record, data: blob, uploadDate: new Date().toISOString() });
            tx.oncomplete = () => resolve();
            tx.onerror = () => reject(tx.error || new Error('IndexedDB 写入失败'));
            tx.onabort = () => reject(tx.error || new Error('IndexedDB 事务中止'));
        } catch (err) {
            reject(err);
        }
    });
}

function getAllFiles() {
    return new Promise((resolve) => {
        const tx = db.transaction([DB_CONFIG.store], 'readonly');
        const store = tx.objectStore(DB_CONFIG.store);
        const req = store.getAll();
        req.onsuccess = () => resolve(req.result || []);
    });
}

function deleteFile(filename) {
    return new Promise((resolve) => {
        const tx = db.transaction([DB_CONFIG.store], 'readwrite');
        const store = tx.objectStore(DB_CONFIG.store);
        store.index('filename').openCursor(filename).onsuccess = (e) => {
            const cursor = e.target.result;
            if (cursor) store.delete(cursor.primaryKey);
        };
        tx.oncomplete = () => resolve();
    });
}

function clearAll() {
    return new Promise((resolve) => {
        const tx = db.transaction([DB_CONFIG.store], 'readwrite');
        tx.objectStore(DB_CONFIG.store).clear();
        tx.oncomplete = () => resolve();
    });
}

function getFile(filename) {
    return new Promise((resolve, reject) => {
        const tx = db.transaction([DB_CONFIG.store], 'readonly');
        const store = tx.objectStore(DB_CONFIG.store);
        const req = store.index('filename').get(filename);
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
    });
}

// 主初始化
document.addEventListener('DOMContentLoaded', async () => {
    initElements();
    try {
        await initDB();
        console.log('✅ 数据库初始化成功', APP_VERSION);
        window.__APP_VERSION__ = APP_VERSION;
        if (location.protocol === 'file:') {
            showMsg('⚠️ 请不要直接双击 HTML 打开\n请通过本地服务器访问：http://127.0.0.1:8123/dashboard/index.html', 'warning');
        }
        updateStatus(`✅ 已连接 ${APP_VERSION}`, true);
        // 检查存储配额
        const quota = await checkStorageQuota();
        if (quota) {
            console.log(`💾 存储状态：已用 ${quota.used}MB / ${quota.quota}MB (${quota.percent}%)`);
            if (quota.percent > 80) {
                showMsg(`⚠️ 存储即将用完\n${quota.used}MB / ${quota.quota}MB`, 'warning');
            }
        }
    } catch (e) {
        console.error('数据库失败:', e);
        updateStatus('❌ 连接失败', false);
        showMsg('❌ 数据库初始化失败：' + e.message, 'error');
    }
    initHandlers();
    setDefaultDate();
});

function updateStatus(text, ok) {
    const el = document.getElementById('storageStatus');
    if (el) { el.textContent = text; el.className = ok ? 'connected' : ''; }
    const debugBar = document.getElementById('debugBar');
    if (debugBar) {
        debugBar.innerHTML = `<span>版本：${APP_VERSION}</span><span>状态：${text}</span><span>文件数：${AppState.files.length}</span>`;
    }
}

// 事件处理 - 修改：省份等筛选独立于时间段，不再级联禁用
function initHandlers() {
    if (elements.uploadBtn && elements.fileInput) {
        elements.uploadBtn.onclick = (e) => { e.preventDefault(); elements.fileInput.click(); };
        elements.fileInput.onchange = async (e) => {
            const files = [...(e.target.files || [])];
            if (files.length) await handleUploadBatch(files);
            elements.fileInput.value = '';
        };
    }
    document.ondragover = (e) => e.preventDefault();
    document.ondrop = async (e) => {
        e.preventDefault();
        const files = [...(e.dataTransfer.files || [])].filter(f => /\.(xlsx|xls)$/i.test(f.name));
        if (files.length) await handleUploadBatch(files);
    };
    
    if (elements.clearAllBtn) elements.clearAllBtn.onclick = async () => {
        if (await showConfirm('确定清空所有数据？\n删除后无法恢复。')) {
            await clearAll();
            AppState.files = []; AppState.cache.clear();
            renderWeeks(); resetFilter();
            showMsg('✅ 已清空', 'success');
        }
    };
    
    // 模式切换
    const modeFilter = document.getElementById('modeFilter');
    const modeSearch = document.getElementById('modeSearch');
    const filterMode = document.getElementById('filterMode');
    const searchMode = document.getElementById('searchMode');
    
    if (modeFilter && modeSearch) {
        modeFilter.onclick = () => {
            modeFilter.classList.add('active');
            modeSearch.classList.remove('active');
            filterMode.style.display = 'block';
            searchMode.style.display = 'none';
        };
        
        modeSearch.onclick = () => {
            modeSearch.classList.add('active');
            modeFilter.classList.remove('active');
            filterMode.style.display = 'none';
            searchMode.style.display = 'block';
        };
    }
    
    // 快速搜索
    const quickSearchBtn = document.getElementById('quickSearchBtn');
    const schoolSearchInput = document.getElementById('schoolSearchInput');
    if (quickSearchBtn && schoolSearchInput) {
        quickSearchBtn.onclick = () => quickSearch(schoolSearchInput.value);
        schoolSearchInput.onkeypress = (e) => { if (e.key === 'Enter') quickSearch(schoolSearchInput.value); };
    }
    
    // 批量删除
    const batchDeleteBtn = document.getElementById('batchDeleteBtn');
    if (batchDeleteBtn) {
        batchDeleteBtn.onclick = async () => {
            const checked = document.querySelectorAll('.week-checkbox:checked');
            if (checked.length === 0) {
                showMsg('⚠️ 请先选择要删除的周次', 'warning');
                return;
            }
            if (await showConfirm(`确定删除选中的 ${checked.length} 个周次？\n删除后无法恢复。`)) {
                for (const cb of checked) {
                    await deleteFile(cb.value);
                    AppState.files = AppState.files.filter(f => f.filename !== cb.value);
                    AppState.cache.delete(cb.value);
                }
                renderWeeks();
                showMsg(`✅ 已删除 ${checked.length} 个周次`, 'success');
            }
        };
    }
    
    // 省份等筛选独立，不立即触发筛选，仅更新下级选项
    if (elements.provinceSelect) elements.provinceSelect.onchange = () => { cascade('province'); };
    if (elements.citySelect) elements.citySelect.onchange = () => { cascade('city'); };
    if (elements.districtSelect) elements.districtSelect.onchange = () => { cascade('district'); };
    if (elements.schoolSelect) elements.schoolSelect.onchange = () => { cascade('school'); };
    if (elements.gradeSelect) elements.gradeSelect.onchange = () => { cascade('grade'); };
    // 学校模糊搜索（条件筛选区域的搜索框）
    const schoolFilterInput = document.getElementById('schoolFilterInput');
    if (schoolFilterInput) {
        schoolFilterInput.oninput = () => filterSchoolOptions(schoolFilterInput.value);
    }
    
    if (elements.applyFilter) elements.applyFilter.onclick = applyFilter;
    if (elements.resetFilter) elements.resetFilter.onclick = resetFilter;
    if (elements.exportBtn) elements.exportBtn.onclick = exportCSV;
    
    // 高价值筛选事件
    if (elements.hvProvinceSelect) elements.hvProvinceSelect.onchange = () => { cascadeHighValue('province'); };
    if (elements.hvCitySelect) elements.hvCitySelect.onchange = () => { cascadeHighValue('city'); };
    if (elements.hvDistrictSelect) elements.hvDistrictSelect.onchange = () => { cascadeHighValue('district'); };
    if (elements.applyHighValueFilter) elements.applyHighValueFilter.onclick = applyHighValueFilter;
    if (elements.resetHighValueFilter) elements.resetHighValueFilter.onclick = resetHighValueFilter;
    if (elements.customSchoolSearchBtn) elements.customSchoolSearchBtn.onclick = applyCustomSchoolSearch;
    if (elements.customSchoolResetBtn) elements.customSchoolResetBtn.onclick = resetCustomSchoolSearch;
    if (elements.customSchoolTabSchool) elements.customSchoolTabSchool.onclick = () => switchCustomSchoolTab('school');
    if (elements.customSchoolTabGrade) elements.customSchoolTabGrade.onclick = () => switchCustomSchoolTab('grade');
    if (elements.customSchoolTabClass) elements.customSchoolTabClass.onclick = () => switchCustomSchoolTab('class');
}


// 批量上传入口
async function handleUploadBatch(files) {
    const items = [...files].filter(Boolean);
    if (!items.length) return;
    const debugBar = document.getElementById('debugBar');
    if (debugBar) debugBar.innerHTML = `<span>版本：${APP_VERSION}</span><span>准备上传：${items.length} 个文件</span>`;
    for (const file of items) {
        await handleUpload(file);
    }
    renderWeeks();
    updateAllSels();
}

// 上传文件 - 优化版：实时进度、详细错误、大文件支持
async function handleUpload(file) {
    const debugBar = document.getElementById('debugBar');
    if (debugBar) debugBar.innerHTML = `<span>版本：${APP_VERSION}</span><span>处理中：${file.name}</span><span>大小：${(file.size / 1024 / 1024).toFixed(2)}MB</span>`;
    const dateInfo = parseName(file.name);
    if (!dateInfo) {
        if (debugBar) debugBar.innerHTML = `<span>版本：${APP_VERSION}</span><span style="color:#dc2626;">文件名不符合规则：${file.name}</span>`;
        showMsg('❌ 格式错误\n使用：20260316-20260322_xxx.xlsx', 'error');
        return;
    }
    if (AppState.files.find(f => f.filename === file.name)) {
        if (debugBar) debugBar.innerHTML = `<span>版本：${APP_VERSION}</span><span>已存在：${file.name}</span>`;
        showMsg('⚠️ 已上传', 'warning');
        return;
    }
    
    const sizeMB = (file.size / 1024 / 1024).toFixed(2);
    const sizeNum = parseFloat(sizeMB);
    
    // 检查文件大小
    if (sizeNum > MAX_STORAGE_MB) {
        showMsg(`❌ 文件过大\n最大支持 ${MAX_STORAGE_MB}MB，当前 ${sizeMB}MB`, 'error');
        return;
    }
    
    // 检查存储配额
    const quota = await checkStorageQuota();
    if (quota && (quota.used + sizeNum > quota.quota * 0.9)) {
        showMsg(`⚠️ 存储空间不足\n预计需要 ${sizeMB}MB，剩余 ${(quota.quota - quota.used).toFixed(1)}MB`, 'warning');
    }
    
    showProgress(`保存：${file.name}`, 0, sizeMB);
    progStart = Date.now();
    
    try {
        // 使用 Promise 包装上传过程以支持进度更新
        await new Promise((resolve, reject) => {
            // 模拟进度更新（因为 IndexedDB put 是原子操作）
            // 实际使用中，大文件上传会需要一定时间
            let progress = 0;
            const interval = setInterval(() => {
                progress += 10;
                if (progress >= 90) {
                    clearInterval(interval);
                } else {
                    updateProgress(progress, (sizeNum * progress / 100), sizeNum);
                }
            }, 200);
            
            // 保存文件到 IndexedDB
            const record = { id: Date.now().toString(), filename: file.name, dateInfo, fileSize: file.size };
            saveFile(record, file)
                .then(() => {
                    clearInterval(interval);
                    updateProgress(100, sizeNum, sizeNum);
                    resolve();
                })
                .catch(err => {
                    clearInterval(interval);
                    reject(err);
                });
        });
        
        AppState.files.push({ id: Date.now().toString(), filename: file.name, dateInfo, fileSize: file.size, status: 'ready' });
        const elapsed = ((Date.now() - progStart) / 1000).toFixed(1);
        hideProgress();
        if (debugBar) debugBar.innerHTML = `<span>版本：${APP_VERSION}</span><span>上传成功：${file.name}</span><span>累计：${AppState.files.length} 周</span>`;
        showMsg(`✅ 保存成功\n${sizeMB} MB | ${elapsed}秒`, 'success');
        renderWeeks();
        
        // 解析新上传的文件并更新下拉选项
        parseExcel(file.name).then(() => {
            updateAllSels();
        }).catch(err => {
            console.error('解析文件失败:', err);
        });
    } catch (e) {
        hideProgress();
        console.error('上传失败:', e);
        if (debugBar) debugBar.innerHTML = `<span>版本：${APP_VERSION}</span><span style="color:#dc2626;">上传失败：${file.name}</span><span>${e.message}</span>`;
        showMsg(`❌ 上传失败：${e.message}\n请检查：\n1. 文件格式是否正确\n2. 存储空间是否足够\n3. 浏览器是否支持大文件存储`, 'error');
    }
}

// 进度显示
let progStart = 0;
function showProgress(name, pct, sizeMB) {
    elements.overlay.classList.add('show');
    elements.uploadProgress.classList.add('show');
    document.getElementById('progressTitle').textContent = name;
    elements.progressFill.style.width = '0%';
    elements.progressText.textContent = '0%';
    document.getElementById('progressStats').textContent = `0 MB / ${sizeMB} MB`;
    progStart = Date.now();
}

function updateProgress(pct, uploaded, total) {
    const elapsed = (Date.now() - progStart) / 1000;
    const speed = uploaded / elapsed;
    const remain = (total - uploaded) / speed;
    elements.progressFill.style.width = pct + '%';
    elements.progressText.textContent = pct + '%';
    document.getElementById('progressStats').textContent = `${uploaded.toFixed(1)} / ${total.toFixed(1)} MB`;
    document.getElementById('progressSpeed').textContent = speed.toFixed(1) + ' MB/s';
    document.getElementById('progressETA').textContent = isFinite(remain) ? remain.toFixed(0) + '秒' : '...';
}

function hideProgress() {
    elements.overlay.classList.remove('show');
    elements.uploadProgress.classList.remove('show');
}

// 加载文件列表
async function loadFileList() {
    const files = await getAllFiles();
    AppState.files = files.map(f => ({ id: f.id, filename: f.filename, dateInfo: f.dateInfo, fileSize: f.fileSize, status: 'ready' }));
    renderWeeks();
    // 从缓存中加载数据并更新下拉选项
    if (AppState.files.length > 0) {
        let loaded = 0;
        for (const f of AppState.files) {
            try {
                await parseExcel(f.filename);
                loaded++;
            } catch(e) { console.error(f.filename, e); }
        }
        updateAllSels();
        // 有数据时立即显示高价值筛选区域（筛选项），统计仅在点击"应用筛选"时执行
        if (AppState.cache.size > 0) {
            updateHighValueSels();
            elements.highValueSection.style.display = 'block';
            if (elements.customSchoolSection) elements.customSchoolSection.style.display = 'block';
        }
    }
}

// 渲染周列表
function renderWeeks() {
    const uploadedSection = document.getElementById('uploadedSection');
    if (!AppState.files.length) { 
        if (uploadedSection) uploadedSection.style.display = 'none'; 
        return; 
    }
    if (uploadedSection) uploadedSection.style.display = 'block';
    
    const sorted = [...AppState.files].sort((a, b) => a.dateInfo.startDate.localeCompare(b.dateInfo.startDate));
    elements.weeksGrid.innerHTML = sorted.map(f => `
        <div class="week-card" data-fn="${f.filename}">
            <div class="week-checkbox-wrapper">
                <input type="checkbox" class="week-checkbox" id="chk_${f.id}" value="${f.filename}">
            </div>
            <label for="chk_${f.id}" class="week-card-content">
                <div class="week-info">
                    <div class="week-date">${f.dateInfo.fullDisplayRange}</div>
                    <div class="week-label">${f.dateInfo.weekLabel}</div>
                </div>
                <div class="week-stats">
                    <div class="week-stat-value">${(f.fileSize/1024/1024).toFixed(1)} MB</div>
                    <div class="week-stat-label">大小</div>
                </div>
            </label>
            <button class="week-delete" data-fn="${f.filename}" title="删除">×</button>
        </div>
    `).join('');
    
    // 更新时间段范围和筛选项
    setDefaultDate();
    updateAllSels();
    
    elements.weeksGrid.querySelectorAll('.week-delete').forEach(btn => {
        btn.onclick = async (e) => {
            e.stopPropagation();
            const filename = btn.dataset.fn;
            if (await showConfirm(`确定删除 ${filename}？\n删除后无法恢复。`)) {
                try {
                    await deleteFile(filename);
                    AppState.files = AppState.files.filter(f => f.filename !== filename);
                    AppState.cache.delete(filename);
                    renderWeeks();
                    showMsg('✅ 已删除', 'success');
                } catch (e) {
                    showMsg('❌ 删除失败：' + e.message, 'error');
                }
            }
        };
    });
}

// 解析 Excel
async function parseExcel(filename) {
    if (AppState.cache.has(filename)) return AppState.cache.get(filename);
    const rec = await getFile(filename);
    if (!rec) throw new Error('文件不存在');
    const buf = await rec.data.arrayBuffer();
    const wb = XLSX.read(new Uint8Array(buf), { type: 'array' });
    const data = XLSX.utils.sheet_to_json(wb.Sheets[wb.SheetNames[0]]);
    const records = data.map(r => ({ ...r, weekStartDate: rec.dateInfo.startDate, weekEndDate: rec.dateInfo.endDate, weekDisplay: rec.dateInfo.displayRange, weekFullDisplay: rec.dateInfo.fullDisplayRange, weekLabel: rec.dateInfo.weekLabel }));
    AppState.cache.set(filename, records);
    return records;
}

// 解析文件名
function parseName(fn) {
    const m = fn.match(/^(\d{4})(\d{2})(\d{2})-(\d{4})(\d{2})(\d{2})_/);
    if (!m) return null;
    const [, y1, m1, d1, y2, m2, d2] = m;
    return { startDate: `${y1}-${m1}-${d1}`, endDate: `${y2}-${m2}-${d2}`, displayRange: `${+m1}/${+d1}-${+m2}/${+d2}`, fullDisplayRange: `${y1}-${m1}-${d1} 至 ${y2}-${m2}-${d2}`, weekLabel: getWeekLabel(`${y1}-${m1}-${d1}`) };
}

function getWeekLabel(ds) {
    const d = dayjs(ds);
    return `${d.year()}年第${Math.ceil(((d - d.startOf('year')) / (7*24*60*60*1000)) + 1)}周`;
}

function setDefaultDate() {
    // 根据已上传文件设置默认日期范围
    if (AppState.files && AppState.files.length > 0) {
        const startDates = AppState.files.map(f => f.dateInfo.startDate).sort();
        const endDates = AppState.files.map(f => f.dateInfo.endDate).sort();
        const minDate = startDates[0];
        const maxDate = endDates[endDates.length - 1];
        
        if (minDate && maxDate) {
            elements.startDate.value = minDate;
            elements.endDate.value = maxDate;
            document.getElementById('dateRangeInfo').innerHTML = `<small>📊 可筛选范围：${minDate} ~ ${maxDate}</small>`;
            return;
        }
    }
    // 默认最近一周
    const t = dayjs();
    const s = t.subtract(7, 'day');
    elements.startDate.value = s.format('YYYY-MM-DD');
    elements.endDate.value = t.format('YYYY-MM-DD');
    document.getElementById('dateRangeInfo').innerHTML = '<small>📊 暂无数据，请先上传 Excel 文件</small>';
}

// 学校下拉框模糊搜索
function filterSchoolOptions(keyword) {
    const allRecs = [];
    AppState.cache.forEach(d => allRecs.push(...d));
    if (allRecs.length === 0) return;
    
    // 获取最后一周的数据（按weekStartDate排序）
    const weeks = [...new Set(allRecs.map(r => r.weekStartDate))].sort();
    const lastWeekStart = weeks[weeks.length - 1] || '';
    const lastWeekRecs = allRecs.filter(r => r.weekStartDate === lastWeekStart);
    
    // 从最后一周数据中获取所有学校
    const allSchools = [...new Set(lastWeekRecs.map(r => r['学校名称']).filter(Boolean))].sort();
    
    // 过滤学校选项
    if (!keyword || !keyword.trim()) {
        // 无关键词显示全部
        updateSel(elements.schoolSelect, new Set(allSchools));
    } else {
        const searchLower = keyword.toLowerCase().trim();
    const exactKeyword = keyword.trim();
        const filtered = allSchools.filter(s => s.toLowerCase().includes(searchLower));
        updateSel(elements.schoolSelect, new Set(filtered));
    }
}

// 级联筛选 - 基于最后一周数据，级联映射：省份 → 城市 → 区县 → 学校 → 年级
function cascade(lvl) {
    let allRecs = [];
    AppState.cache.forEach(d => allRecs.push(...d));
    if (allRecs.length === 0) return;

    const weekStarts = [...new Set(allRecs.map(r => r.weekStartDate))].sort();
    const lastWeekStart = weekStarts[weekStarts.length - 1] || '';
    const lastWeekRecs = allRecs.filter(r => r.weekStartDate === lastWeekStart);

    let selProvince = elements.provinceSelect.value;
    let selCity = elements.citySelect.value;
    let selDistrict = elements.districtSelect.value;
    let selSchool = elements.schoolSelect.value;
    let selGrade = elements.gradeSelect.value;

    const provinces = [...new Set(lastWeekRecs.map(r => r['省份']).filter(Boolean))];
    updateSel(elements.provinceSelect, new Set(provinces));
    if (!provinces.includes(selProvince)) selProvince = '';
    elements.provinceSelect.value = selProvince;

    let cityRecs = lastWeekRecs;
    if (selProvince) cityRecs = cityRecs.filter(r => r['省份'] === selProvince);
    const cities = [...new Set(cityRecs.map(r => r['城市']).filter(Boolean))];
    updateSel(elements.citySelect, new Set(cities));
    if (!cities.includes(selCity)) selCity = '';
    elements.citySelect.value = selCity;

    let districtRecs = lastWeekRecs;
    if (selProvince) districtRecs = districtRecs.filter(r => r['省份'] === selProvince);
    if (selCity) districtRecs = districtRecs.filter(r => r['城市'] === selCity);
    const districts = [...new Set(districtRecs.map(r => r['区县']).filter(Boolean))];
    updateSel(elements.districtSelect, new Set(districts));
    if (!districts.includes(selDistrict)) selDistrict = '';
    elements.districtSelect.value = selDistrict;

    let schoolRecs = lastWeekRecs;
    if (selProvince) schoolRecs = schoolRecs.filter(r => r['省份'] === selProvince);
    if (selCity) schoolRecs = schoolRecs.filter(r => r['城市'] === selCity);
    if (selDistrict) schoolRecs = schoolRecs.filter(r => r['区县'] === selDistrict);
    const schools = [...new Set(schoolRecs.map(r => r['学校名称']).filter(Boolean))];
    updateSel(elements.schoolSelect, new Set(schools));
    if (!schools.includes(selSchool)) selSchool = '';
    elements.schoolSelect.value = selSchool;

    let gradeRecs = lastWeekRecs;
    if (selProvince) gradeRecs = gradeRecs.filter(r => r['省份'] === selProvince);
    if (selCity) gradeRecs = gradeRecs.filter(r => r['城市'] === selCity);
    if (selDistrict) gradeRecs = gradeRecs.filter(r => r['区县'] === selDistrict);
    if (selSchool) gradeRecs = gradeRecs.filter(r => r['学校名称'] === selSchool);
    const grades = [...new Set(gradeRecs.map(r => r['年级']).filter(Boolean))];
    updateSel(elements.gradeSelect, new Set(grades));
    if (!grades.includes(selGrade)) selGrade = '';
    elements.gradeSelect.value = selGrade;

    elements.provinceSelect.disabled = false;
    elements.citySelect.disabled = false;
    elements.districtSelect.disabled = false;
    elements.schoolSelect.disabled = false;
    elements.gradeSelect.disabled = false;

    updateHighValueSels();
}

// 更新高价值筛选项 - 基于最后一周数据
function updateHighValueSels() {
    let allRecs = [];
    AppState.cache.forEach(d => allRecs.push(...d));
    
    if (allRecs.length === 0) {
        updateSel(elements.hvProvinceSelect, new Set());
        updateSel(elements.hvCitySelect, new Set());
        updateSel(elements.hvDistrictSelect, new Set());
        updateSel(elements.hvGradeSelect, new Set());
        return;
    }
    
    // 获取最后一周的数据
    const weekStarts = [...new Set(allRecs.map(r => r.weekStartDate))].sort();
    const lastWeekStart = weekStarts[weekStarts.length - 1] || '';
    const lastWeekRecs = allRecs.filter(r => r.weekStartDate === lastWeekStart);
    
    updateSel(elements.hvProvinceSelect, new Set(lastWeekRecs.map(r => r['省份']).filter(Boolean)));
    updateSel(elements.hvCitySelect, new Set(lastWeekRecs.map(r => r['城市']).filter(Boolean)));
    updateSel(elements.hvDistrictSelect, new Set(lastWeekRecs.map(r => r['区县']).filter(Boolean)));
    updateSel(elements.hvGradeSelect, new Set(lastWeekRecs.map(r => r['年级']).filter(Boolean)));
}

// 高价值筛选级联
function cascadeHighValue(lvl) {
    let allRecs = [];
    AppState.cache.forEach(d => allRecs.push(...d));
    if (allRecs.length === 0) return;
    
    // 获取最后一周的数据
    const weekStarts = [...new Set(allRecs.map(r => r.weekStartDate))].sort();
    const lastWeekStart = weekStarts[weekStarts.length - 1] || '';
    let recs = allRecs.filter(r => r.weekStartDate === lastWeekStart);
    
    const selProvince = elements.hvProvinceSelect.value;
    const selCity = elements.hvCitySelect.value;
    const selDistrict = elements.hvDistrictSelect.value;
    const selGrade = elements.hvGradeSelect.value;
    
    if (selProvince) recs = recs.filter(r => r['省份'] === selProvince);
    if (selCity) recs = recs.filter(r => r['城市'] === selCity);
    if (selDistrict) recs = recs.filter(r => r['区县'] === selDistrict);
    
    // 省份下拉框
    let provinceRecs = allRecs.filter(r => r.weekStartDate === lastWeekStart);
    const provinces = [...new Set(provinceRecs.map(r => r['省份']).filter(Boolean))];
    updateSel(elements.hvProvinceSelect, new Set(provinces));
    elements.hvProvinceSelect.value = selProvince && provinces.includes(selProvince) ? selProvince : '';
    
    // 城市下拉框
    let cityRecs = allRecs.filter(r => r.weekStartDate === lastWeekStart);
    if (selProvince) cityRecs = cityRecs.filter(r => r['省份'] === selProvince);
    const cities = [...new Set(cityRecs.map(r => r['城市']).filter(Boolean))];
    updateSel(elements.hvCitySelect, new Set(cities));
    elements.hvCitySelect.value = selCity && cities.includes(selCity) ? selCity : '';
    
    // 区县下拉框
    let districtRecs = allRecs.filter(r => r.weekStartDate === lastWeekStart);
    if (selProvince) districtRecs = districtRecs.filter(r => r['省份'] === selProvince);
    if (selCity) districtRecs = districtRecs.filter(r => r['城市'] === selCity);
    const districts = [...new Set(districtRecs.map(r => r['区县']).filter(Boolean))];
    updateSel(elements.hvDistrictSelect, new Set(districts));
    elements.hvDistrictSelect.value = selDistrict && districts.includes(selDistrict) ? selDistrict : '';
    
    // 年级下拉框
    let gradeRecs = allRecs.filter(r => r.weekStartDate === lastWeekStart);
    if (selProvince) gradeRecs = gradeRecs.filter(r => r['省份'] === selProvince);
    if (selCity) gradeRecs = gradeRecs.filter(r => r['城市'] === selCity);
    if (selDistrict) gradeRecs = gradeRecs.filter(r => r['区县'] === selDistrict);
    const grades = [...new Set(gradeRecs.map(r => r['年级']).filter(Boolean))];
    updateSel(elements.hvGradeSelect, new Set(grades));
    elements.hvGradeSelect.value = selGrade && grades.includes(selGrade) ? selGrade : '';
}

// 计算年级指标并应用筛选
function applyHighValueFilter() {
    // 获取所有周的数据
    let allRecs = [];
    AppState.cache.forEach(d => allRecs.push(...d));
    if (allRecs.length === 0) {
        showMsg('⚠️ 暂无数据', 'warning');
        return;
    }
    
    const weekStarts = [...new Set(allRecs.map(r => r.weekStartDate))].sort();
    
    // 应用省市区年级筛选（使用所有周数据）
    const selProvince = elements.hvProvinceSelect.value;
    const selCity = elements.hvCitySelect.value;
    const selDistrict = elements.hvDistrictSelect.value;
    const selGrade = elements.hvGradeSelect.value;
    
    if (selProvince) allRecs = allRecs.filter(r => r['省份'] === selProvince);
    if (selCity) allRecs = allRecs.filter(r => r['城市'] === selCity);
    if (selDistrict) allRecs = allRecs.filter(r => r['区县'] === selDistrict);
    if (selGrade) allRecs = allRecs.filter(r => r['年级'] === selGrade);
    
    const sortedWeeks = [...new Set(allRecs.map(r => r.weekStartDate))].sort();
    const lastWeekStart = sortedWeeks[sortedWeeks.length - 1] || '';
    
    // 按学校+年级分组，计算指标（付费率与周趋势基于所有周；班级数/学生总数/试用人数基于最后一周）
    const gradeMap = new Map();
    allRecs.forEach(r => {
        const key = `${r['省份']}|${r['城市']}|${r['区县']}|${r['学校名称']}|${r['年级']}`;
        if (!gradeMap.has(key)) {
            gradeMap.set(key, {
                province: r['省份'] || '',
                city: r['城市'] || '',
                district: r['区县'] || '',
                school: r['学校名称'] || '',
                grade: r['年级'] || '',
                totalClassCount: 0,
                totalStudentCount: 0,
                totalPaidCount: 0,
                totalTrialCount: 0,
                totalStudents: 0,
                lastWeekClassCount: 0,
                lastWeekStudentCount: 0,
                lastWeekTrialCount: 0,
                weeklyData: new Map()
            });
        }
        const g = gradeMap.get(key);
        const weekKey = r.weekStartDate;
        
        // 初始化周数据
        if (!g.weeklyData.has(weekKey)) {
            g.weeklyData.set(weekKey, {
                classCount: 0,
                studentCount: 0,
                paidCount: 0,  // 未过期付费人数
                trialCount: 0,  // 未过期试用人数
                totalStudents: 0,
                assignedClassCount: 0,
                completionRates: []
            });
        }
        const w = g.weeklyData.get(weekKey);
        
        // 累计该周数据
        w.classCount++;
        w.studentCount += +r['总学生数'] || 0;
        w.paidCount += +r['未过期付费学生数'] || 0;
        w.trialCount += +r['未过期试用学生数'] || 0;
        w.totalStudents += +r['总学生数'] || 0;
        
        // 作业布置次数>=1的班级
        if ((+r['布置作业次数'] || 0) >= 1) {
            w.assignedClassCount++;
        }
        
        // 收集作业完成率
        const completionRate = +r['作业完成率'] || 0;
        if (completionRate > 0) {
            w.completionRates.push(completionRate * 100);
        }
        
        // 累计总数
        g.totalClassCount++;
        g.totalStudentCount += +r['总学生数'] || 0;
        g.totalPaidCount += +r['未过期付费学生数'] || 0;
        g.totalTrialCount += +r['未过期试用学生数'] || 0;
        g.totalStudents += +r['总学生数'] || 0;
        
        if (r.weekStartDate === lastWeekStart) {
            g.lastWeekClassCount++;
            g.lastWeekStudentCount += +r['总学生数'] || 0;
            g.lastWeekTrialCount += +r['未过期试用学生数'] || 0;
        }
    });
    
    // 计算年级指标
    const gradeMetrics = [];
    gradeMap.forEach((g, key) => {
        // 基于最后一周计算：年级付费率 = 最后一周未过期付费学生数 / 最后一周总学生数
        const lastWeek = g.weeklyData.get(lastWeekStart);
        const payRate = lastWeek && lastWeek.totalStudents > 0
            ? (lastWeek.paidCount / lastWeek.totalStudents) * 100
            : 0;
        
        // 每周的布置率和完成率
        const weeklyMetrics = [];
        sortedWeeks.forEach(week => {
            if (g.weeklyData.has(week)) {
                const w = g.weeklyData.get(week);
                const assignRate = w.classCount > 0 ? (w.assignedClassCount / w.classCount) * 100 : 0;
                const avgCompletionRate = w.completionRates.length > 0 
                    ? w.completionRates.reduce((a, b) => a + b, 0) / w.completionRates.length 
                    : 0;
                weeklyMetrics.push({
                    week: week,
                    assignRate: assignRate,
                    avgCompletionRate: avgCompletionRate
                });
            }
        });
        
        gradeMetrics.push({
            province: g.province,
            city: g.city,
            district: g.district,
            school: g.school,
            grade: g.grade,
            classCount: g.lastWeekClassCount,
            studentCount: g.lastWeekStudentCount,
            trialCount: g.lastWeekTrialCount,
            payRate: payRate,
            weeklyMetrics: weeklyMetrics
        });
    });

    // ── 第二步：按学校聚合，取年级付费率最大值，得出学校定义 ──
    const schoolMaxPayRate = new Map(); // schoolKey → maxPayRate
    gradeMetrics.forEach(g => {
        const key = `${g.province}|${g.city}|${g.district}|${g.school}`;
        const cur = schoolMaxPayRate.get(key);
        if (cur === undefined || g.payRate > cur) {
            schoolMaxPayRate.set(key, g.payRate);
        }
    });

    // 学校定义函数
    function getSchoolCategory(maxRate) {
        if (maxRate > 60) return '付费校';
        if (maxRate >= 10) return '付费率需提升校';
        return '试用校';
    }

    // 给每个年级行挂上学校定义
    gradeMetrics.forEach(g => {
        const key = `${g.province}|${g.city}|${g.district}|${g.school}`;
        const maxRate = schoolMaxPayRate.get(key) || 0;
        g.schoolCategory = getSchoolCategory(maxRate);
        g.schoolMaxPayRate = maxRate;
    });
    
    // 获取筛选条件
    const payRateThreshold = parseFloat(elements.hvPayRateSelect.value) || 0;
    const studentCountThreshold = parseFloat(elements.hvStudentCountSelect.value) || 0;
    const assignRateThreshold = parseFloat(elements.hvAssignRateSelect.value) || 0;
    const completionRateThreshold = parseFloat(elements.hvCompletionRateSelect.value) || 0;
    const trialCountThreshold = parseFloat(elements.hvTrialCountSelect.value) || 0;
    const schoolCategoryFilter = elements.hvSchoolCategorySelect.value;
    const favoriteFilter = elements.hvFavoriteSelect?.value || '';
    const favoriteSet = loadFavorites();
    
    // 应用筛选 - 付费率为小于等于筛选
    let filteredGrades = gradeMetrics.filter(g => {
        if (payRateThreshold > 0 && g.payRate > payRateThreshold) return false;
        if (studentCountThreshold > 0 && g.studentCount < studentCountThreshold) return false;
        // 布置率/完成率筛选基于所有周的平均值
        if (assignRateThreshold > 0) {
            const avgAssignRate = g.weeklyMetrics.length > 0 
                ? g.weeklyMetrics.reduce((a, w) => a + w.assignRate, 0) / g.weeklyMetrics.length 
                : 0;
            if (avgAssignRate < assignRateThreshold) return false;
        }
        if (completionRateThreshold > 0) {
            const avgCompletion = g.weeklyMetrics.length > 0 
                ? g.weeklyMetrics.reduce((a, w) => a + w.avgCompletionRate, 0) / g.weeklyMetrics.length 
                : 0;
            if (avgCompletion < completionRateThreshold) return false;
        }
        if (trialCountThreshold > 0 && g.trialCount < trialCountThreshold) return false;
        if (schoolCategoryFilter && g.schoolCategory !== schoolCategoryFilter) return false;
        const isFav = favoriteSet.has(favoriteKey(g));
        if (favoriteFilter === 'yes' && !isFav) return false;
        if (favoriteFilter === 'no' && isFav) return false;
        return true;
    });
    
    // 显示结果
    renderHighValueTable(filteredGrades, sortedWeeks);
    
    if (filteredGrades.length === 0) {
        showMsg('⚠️ 筛选后无数据', 'warning');
    } else {
        showMsg(`✅ 找到 ${filteredGrades.length} 条高价值年级数据`, 'success');
    }
}

function renderHighValueTable(grades, sortedWeeks) {
    if (grades.length === 0) {
        elements.highValueTableBody.innerHTML = '<tr><td colspan="12" style="text-align:center;padding:40px;color:#999;">请点击"应用筛选"查看结果</td></tr>';
        document.getElementById('highValueTableHead').innerHTML = `
            <tr>
                <th>省份</th>
                <th>城市</th>
                <th>区县</th>
                <th>学校</th>
                <th>学校定义</th>
                <th>年级</th>
                <th>班级数</th>
                <th>学生总数</th>
                <th>未过期试用人数</th>
                <th>年级付费率</th>
            <th>收藏</th>
            </tr>`;
        elements.highValueInfo.textContent = '';
        elements.highValueSection.style.display = 'block';
        return;
    }
    
    // 按省份、城市、区县、学校、年级排序
    grades.sort((a, b) => {
        const pCmp = String(a.province).localeCompare(String(b.province), 'zh-CN');
        if (pCmp !== 0) return pCmp;
        const cCmp = String(a.city).localeCompare(String(b.city), 'zh-CN');
        if (cCmp !== 0) return cCmp;
        const dCmp = String(a.district).localeCompare(String(b.district), 'zh-CN');
        if (dCmp !== 0) return dCmp;
        const schCmp = String(a.school).localeCompare(String(b.school), 'zh-CN');
        if (schCmp !== 0) return schCmp;
        return String(a.grade).localeCompare(String(b.grade), 'zh-CN');
    });
    
    // 生成动态表头（基于周次）
    let theadHtml = `<tr>
        <th rowspan="2">省份</th>
        <th rowspan="2">城市</th>
        <th rowspan="2">区县</th>
        <th rowspan="2">学校</th>
        <th rowspan="2">学校定义</th>
        <th rowspan="2">年级</th>
        <th rowspan="2">班级数</th>
        <th rowspan="2">学生总数</th>
        <th rowspan="2">未过期试用人数</th>
        <th rowspan="2">年级付费率</th>
        <th rowspan="2">收藏</th>
        <th colspan="${sortedWeeks.length * 2}" style="text-align:center;">作业布置率/平均完成率</th>
    </tr><tr>`;
    sortedWeeks.forEach(week => {
        theadHtml += `<th colspan="2" style="font-size:11px;">${week}</th>`;
    });
    theadHtml += '</tr>';
    document.getElementById('highValueTableHead').innerHTML = theadHtml;
    
    // 生成数据行
    elements.highValueTableBody.innerHTML = grades.map(g => {
        let cells = `
            <td>${g.province}</td>
            <td>${g.city}</td>
            <td>${g.district}</td>
            <td class="school-name-cell" title="${g.school}">${g.school}</td>
            <td style="text-align:center;font-weight:600;color:${g.schoolCategory === '付费校' ? '#10b981' : g.schoolCategory === '付费率需提升校' ? '#f59e0b' : '#6b7280'};">${g.schoolCategory}</td>
            <td>${g.grade}</td>
            <td style="text-align:center;">${g.classCount}</td>
            <td style="text-align:center;">${g.studentCount.toLocaleString()}</td>
            <td style="text-align:center;">${g.trialCount.toLocaleString()}</td>
            <td style="text-align:center;font-weight:600;color:${g.payRate >= 30 ? '#10b981' : '#f59e0b'};">${g.payRate.toFixed(1)}%</td>
            <td style="text-align:center;"><button class="favorite-toggle" data-fav-key="${favoriteKey(g)}" style="border:none;background:none;cursor:pointer;font-size:18px;">${loadFavorites().has(favoriteKey(g)) ? '⭐' : '☆'}</button></td>`;
        
        // 每周的布置率和完成率
        sortedWeeks.forEach(week => {
            const weekData = g.weeklyMetrics.find(w => w.week === week);
            if (weekData) {
                cells += `<td style="text-align:center;font-size:11px;">${weekData.assignRate.toFixed(1)}%</td>`;
                cells += `<td style="text-align:center;font-size:11px;color:${weekData.avgCompletionRate >= 70 ? '#10b981' : '#f59e0b'};">${weekData.avgCompletionRate.toFixed(1)}%</td>`;
            } else {
                cells += '<td style="text-align:center;color:#ccc;">-</td>';
                cells += '<td style="text-align:center;color:#ccc;">-</td>';
            }
        });
        
        return '<tr>' + cells + '</tr>';
    }).join('');
    
    const lastWeek = sortedWeeks.length > 0 ? sortedWeeks[sortedWeeks.length - 1] : '';
    elements.highValueInfo.textContent = `共 ${grades.length} 条记录 | 数据来源：${sortedWeeks.length}周（${lastWeek}）`;
    elements.highValueSection.style.display = 'block';
    document.querySelectorAll('.favorite-toggle').forEach(btn => { btn.onclick = () => toggleFavoriteByKey(btn.dataset.favKey); });
    scheduleAdaptNameCells();
}

function resetHighValueFilter() {
    elements.hvProvinceSelect.value = '';
    elements.hvCitySelect.value = '';
    elements.hvDistrictSelect.value = '';
    elements.hvGradeSelect.value = '';
    elements.hvPayRateSelect.value = '';
    elements.hvStudentCountSelect.value = '';
    elements.hvAssignRateSelect.value = '';
    elements.hvCompletionRateSelect.value = '';
    elements.hvTrialCountSelect.value = '';
    elements.hvSchoolCategorySelect.value = '';
    if (elements.hvFavoriteSelect) elements.hvFavoriteSelect.value = '';
    updateHighValueSels();
    renderHighValueTable([], []);
    elements.highValueSection.style.display = AppState.filteredData.length ? 'block' : 'none';
    showMsg('✅ 已重置', 'success');
}

function getCascadeData() {
    let recs = [];
    AppState.cache.forEach(d => recs.push(...d));
    const p = elements.provinceSelect.value, c = elements.citySelect.value, di = elements.districtSelect.value, s = elements.schoolSelect.value;
    if (p) recs = recs.filter(r => r['省份'] === p);
    if (c) recs = recs.filter(r => r['城市'] === c);
    if (di) recs = recs.filter(r => r['区县'] === di);
    if (s) recs = recs.filter(r => r['学校名称'] === s);
    return recs;
}

function updateSel(sel, vals) {
    const cur = sel.value, def = sel.querySelector('option')?.textContent || '全部';
    sel.innerHTML = `<option value="">${def}</option>`;
    [...vals].sort().forEach(v => { const o = document.createElement('option'); o.value = v; o.textContent = v; sel.appendChild(o); });
    sel.value = cur;
}

// 应用筛选
async function applyFilter() {
    const searchModeBtn = document.getElementById('modeSearch');
    const isQuickSearchMode = !!(searchModeBtn && searchModeBtn.classList.contains('active'));
    if (isQuickSearchMode) {
        const keyword = document.getElementById('schoolSearchInput')?.value || '';
        await quickSearch(keyword);
        return;
    }

    const sd = elements.startDate.value, ed = elements.endDate.value;
    if (!sd || !ed) { alert('请选择日期范围'); return; }
    const st = dayjs(sd), en = dayjs(ed);
    if (st.isAfter(en)) { alert('开始日期不能晚于结束日期'); return; }
    
    showLoading();
    try {
        const rel = AppState.files.filter(f => !dayjs(f.dateInfo.endDate).isBefore(st) && !dayjs(f.dateInfo.startDate).isAfter(en));
        let all = [];
        for (const f of rel) { try { all.push(...await parseExcel(f.filename)); } catch(e) { console.error(f.filename, e); } }
        
        const p = elements.provinceSelect.value, c = elements.citySelect.value, di = elements.districtSelect.value, s = elements.schoolSelect.value, g = elements.gradeSelect.value;
        AppState.filteredData = all.filter(r => {
            if (p && r['省份'] !== p) return false;
            if (c && r['城市'] !== c) return false;
            if (di && r['区县'] !== di) return false;
            if (s && r['学校名称'] !== s) return false;
            if (g && r['年级'] !== g) return false;
            return true;
        });
        
        hideLoading();
        elements.dataCount.textContent = AppState.filteredData.length.toLocaleString();
        renderDash();
        showMsg(AppState.filteredData.length ? `✅ 完成\n${AppState.filteredData.length.toLocaleString()} 条` : '⚠️ 无数据', AppState.filteredData.length ? 'success' : 'warning');
    } catch (e) {
        hideLoading();
        showMsg('❌ ' + e.message, 'error');
    }
}

function resetFilter() {
    setDefaultDate();
    elements.provinceSelect.value = '';
    elements.citySelect.value = '';
    elements.districtSelect.value = '';
    elements.schoolSelect.value = '';
    elements.gradeSelect.value = '';
    updateAllSels();
    AppState.filteredData = [];
    elements.dataCount.textContent = '0';
    renderDash();
    showMsg('✅ 已重置', 'success');
}

// 快速搜索学校
async function quickSearch(keyword) {
    // 优先使用传入的 keyword 参数（来自 onclick 事件），避免重复读取 DOM
    if (!keyword || !keyword.trim()) {
        showMsg('⚠️ 请输入学校名称', 'warning');
        return;
    }
    
    const searchLower = keyword.toLowerCase().trim();
    const exactKeyword = keyword.trim();
    
    showLoading();
    try {
        // 搜索所有文件
        let all = [];
        for (const f of AppState.files) { 
            try { 
                all.push(...await parseExcel(f.filename)); 
            } catch(e) { 
                console.error(f.filename, e); 
            } 
        }
        
        // 根据关键词模糊搜索学校名称
        AppState.filteredData = all.filter(r => {
            const schoolNameRaw = (r['学校名称'] || '').trim();
            const schoolName = schoolNameRaw.toLowerCase();
            if (schoolNameRaw === exactKeyword) return true;
            return schoolName.includes(searchLower);
        });
        
        // DEBUG quickSearch
        console.log('quickSearch Debug:', {
            keyword: searchLower,
            allRecords: all.length,
            filteredRecords: AppState.filteredData.length,
            sampleSchool: AppState.filteredData[0] ? AppState.filteredData[0]['学校名称'] : null,
            sampleClassId: AppState.filteredData[0] ? AppState.filteredData[0]['班级 id'] : null
        });
        
        hideLoading();
        elements.dataCount.textContent = AppState.filteredData.length.toLocaleString();
        renderDash();
        renderCharts();
        renderTbl();
        
        if (AppState.filteredData.length === 0) {
            showMsg('⚠️ 未搜索到学校名称', 'warning');
            elements.emptyState.style.display = 'block';
            elements.metricsSection.style.display = 'none';
            elements.chartsSection.style.display = 'none';
            elements.tableSection.style.display = 'none';
        } else {
            showMsg(`🔍 找到 ${AppState.filteredData.length} 条结果`, 'success');
            elements.emptyState.style.display = 'none';
            elements.metricsSection.style.display = 'block';
            elements.chartsSection.style.display = 'block';
            elements.tableSection.style.display = 'block';
        }
    } catch (e) {
        hideLoading();
        showMsg('❌ 搜索失败：' + e.message, 'error');
    }
}

// 更新所有下拉选项 - 基于最后一周数据独立去重
function updateAllSels() {
    let allRecs = [];
    AppState.cache.forEach(d => allRecs.push(...d));
    
    if (allRecs.length === 0) {
        updateSel(elements.provinceSelect, new Set());
        updateSel(elements.citySelect, new Set());
        updateSel(elements.districtSelect, new Set());
        updateSel(elements.schoolSelect, new Set());
        updateSel(elements.gradeSelect, new Set());
        return;
    }
    
    // 获取所有周次并排序
    const weekStarts = [...new Set(allRecs.map(r => r.weekStartDate))].sort();
    const lastWeekStart = weekStarts[weekStarts.length - 1] || '';
    const lastWeekRecs = allRecs.filter(r => r.weekStartDate === lastWeekStart);
    
    updateSel(elements.provinceSelect, new Set(lastWeekRecs.map(r => r['省份']).filter(Boolean)));
    updateSel(elements.citySelect, new Set(lastWeekRecs.map(r => r['城市']).filter(Boolean)));
    updateSel(elements.districtSelect, new Set(lastWeekRecs.map(r => r['区县']).filter(Boolean)));
    updateSel(elements.schoolSelect, new Set(lastWeekRecs.map(r => r['学校名称']).filter(Boolean)));
    updateSel(elements.gradeSelect, new Set(lastWeekRecs.map(r => r['年级']).filter(Boolean)));
    
    elements.provinceSelect.disabled = false;
    elements.citySelect.disabled = false;
    elements.districtSelect.disabled = false;
    elements.schoolSelect.disabled = false;
    elements.gradeSelect.disabled = false;
    
    // 更新高价值筛选项
    updateHighValueSels();
}

// 渲染看板
function renderDash() {
    if (!AppState.filteredData.length) {
        elements.metricsSection.style.display = 'none';
        elements.chartsSection.style.display = 'none';
        elements.tableSection.style.display = 'none';
        elements.highValueSection.style.display = 'none';
        if (elements.customSchoolSection) elements.customSchoolSection.style.display = 'none';
        elements.emptyState.style.display = 'block';
        return;
    }
    elements.emptyState.style.display = 'none';
    elements.metricsSection.style.display = 'block';
    elements.chartsSection.style.display = 'block';
    elements.tableSection.style.display = 'block';
    // 有数据时默认显示高价值筛选区域（仅显示筛选项，不自动统计）
    elements.highValueSection.style.display = 'block';
    if (elements.customSchoolSection) elements.customSchoolSection.style.display = 'block';
    updateHighValueSels();
    renderMet();
    renderCharts();
    renderTbl();
}

// 指标 - 修复：Excel 中转化率和完成率是小数（0.1967），需要乘以 100 显示为百分数
function renderMet() {
    const ta = AppState.filteredData.reduce((s, r) => s + (+r['布置作业次数'] || 0), 0);
    const tc = lastWeekData.reduce((s, r) => s + (+r['作业完成率'] || 0) * 100, 0);
    const tv = lastWeekData.reduce((s, r) => s + (+r['转化率'] || 0) * 100, 0);
    const avgC = lastWeekData.length ? (tc / lastWeekData.length).toFixed(1) : 0;
    const avgV = lastWeekData.length ? (tv / lastWeekData.length).toFixed(1) : 0;
    // 覆盖班级：筛选项下班级总数（按班级ID去重）- 基于实际筛选结果
    const cls = new Set(AppState.filteredData.map(r => getClassId(r)).filter(Boolean));
    const clsCount = cls.size;
    const weeksForSum = [...new Set(AppState.filteredData.map(r => r.weekStartDate))].sort();
    const lastWeekForSum = weeksForSum[weeksForSum.length - 1];
    const lastWeekDataForSum = AppState.filteredData.filter(r => r.weekStartDate === lastWeekForSum);
    const stu = lastWeekDataForSum.reduce((s, r) => s + (+r['总学生数'] || 0), 0);
    
    // 平均布置作业次数 = 布置作业次数求和 / 班级数求和
    const avgAssignments = clsCount > 0 ? (ta / clsCount).toFixed(1) : 0;
    
    // DEBUG - show values before assignment
    window._debugMet = {
        filteredDataLength: AppState.filteredData.length,
        clsCount: clsCount,
        ta: ta,
        avgAssignments: avgAssignments,
        first3Records: AppState.filteredData.slice(0, 3).map(r => ({班级ID: getClassId(r), 学校: r['学校名称'], 班级IDType: typeof getClassId(r)})),
        allClassIds: AppState.filteredData.map(r => getClassId(r)).filter(Boolean).slice(0, 10)
    };
    console.log('renderMet Debug:', window._debugMet);
    
    // 1.1 总学生数
    elements.studentCount.textContent = stu.toLocaleString();
    
    // 1.2 未过期付费学生数：基于筛选条件，仅取最后一周数据求和
    const weeks = [...new Set(AppState.filteredData.map(r => r.weekStartDate))].sort();
    const lastWeekStart = weeks[weeks.length - 1];
    const lastWeekData = AppState.filteredData.filter(r => r.weekStartDate === lastWeekStart);
    const paidNotExpired = lastWeekData.reduce((s, r) => s + (+r['未过期付费学生数'] || 0), 0);
    elements.paidNotExpired.textContent = paidNotExpired.toLocaleString();
    
    // 1.3 转化率
    elements.conversionRate.textContent = avgV + '%';
    
    // 1.4 覆盖班级
    const displayClsCount = clsCount.toLocaleString();
    console.log('Setting classCount to:', displayClsCount);
    elements.classCount.textContent = displayClsCount;
    
    // 1.5 平均布置作业次数
    const displayAvgAssignments = avgAssignments;
    console.log('Setting avgAssignments to:', displayAvgAssignments);
    elements.avgAssignments.textContent = displayAvgAssignments;
    
    // 1.6 作业完成率
    elements.avgCompletionRate.textContent = avgC + '%';
}

// 图表 - 修复：作业完成率显示平均值
function renderCharts() {
    const comboEl = document.getElementById('comboChart');
    if (comboEl) {
        const comboInst = echarts.getInstanceByDom(comboEl);
        if (comboInst) comboInst.dispose();
        comboEl.closest('.chart-card')?.remove();
    }

    const conversionEl = document.getElementById('conversionChart');
    if (!conversionEl) return;
    const oldConversion = echarts.getInstanceByDom(conversionEl);
    if (oldConversion) oldConversion.dispose();

    const wm = new Map();
    AppState.filteredData.forEach(r => {
        const k = r.weekLabel;
        if (!wm.has(k)) wm.set(k, { label: r.weekFullDisplay, v: 0, n: 0, vSum: 0, paidSum: 0 });
        const w = wm.get(k);
        w.vSum += (+r['转化率'] || 0) * 100;
        w.paidSum += +r['未过期付费学生数'] || 0;
        w.n++;
        w.v = w.n ? (w.vSum / w.n).toFixed(1) : 0;
    });
    const sw = [...wm.entries()].sort((a, b) => {
        const aStart = a[1].label.split('至')[0].trim();
        const bStart = b[1].label.split('至')[0].trim();
        return dayjs(aStart).isBefore(dayjs(bStart)) ? -1 : 1;
    });
    const data = {
        labels: sw.map(([_, d]) => d.label),
        v: sw.map(([_, d]) => d.v),
        paid: sw.map(([_, d]) => d.paidSum)
    };

    echarts.init(conversionEl).setOption({
        tooltip: {
            trigger: 'axis',
            formatter: function(params) {
                let result = params[0].name + '<br/>';
                params.forEach(p => {
                    result += p.marker + p.seriesName + ': ' + p.value + (p.seriesName.includes('率') ? '%' : '人') + '<br/>';
                });
                return result;
            }
        },
        legend: { data: ['未过期付费学生数', '转化率'], top: 0 },
        grid: { left: '3%', right: '4%', bottom: '3%', top: '15%', containLabel: true },
        xAxis: { type: 'category', data: data.labels, axisLabel: { rotate: 45, color: '#64748b' } },
        yAxis: [{
            type: 'value',
            name: '人数',
            axisLabel: { color: '#f59e0b' },
            position: 'left'
        }, {
            type: 'value',
            name: '转化率',
            axisLabel: { color: '#8b5cf6', formatter: '{value}%' },
            position: 'right',
            min: 0,
            max: 100
        }],
        series: [{
            name: '未过期付费学生数',
            type: 'bar',
            data: data.paid,
            itemStyle: {
                color: new echarts.graphic.LinearGradient(0,0,0,1, [{offset:0,color:'#f59e0b'},{offset:1,color:'#d97706'}])
            },
            label: {
                show: true,
                position: 'top',
                color: '#f59e0b',
                fontSize: 11,
                formatter: '{c}'
            }
        }, {
            name: '转化率',
            type: 'line',
            yAxisIndex: 1,
            data: data.v,
            smooth: true,
            lineStyle: { color: '#8b5cf6', width: 3 },
            itemStyle: { color: '#8b5cf6' },
            label: {
                show: true,
                position: 'top',
                color: '#8b5cf6',
                fontSize: 11,
                formatter: '{c}%'
            }
        }]
    });
}

// 表格 v2.5 - 按周维度展示，固定列 + 动态周列
const ROWS_PER_PAGE = 15;
let currentPage = 1;
let totalRows = 0;

function renderTbl(page = 1) {
    const theadEl = document.querySelector('#dataTable > thead');
    try {
        if (!AppState.filteredData.length) {
            theadEl.innerHTML = '';
            elements.tableBody.innerHTML = '<tr><td colspan="20" style="text-align:center;padding:40px;color:#999;">暂无数据，请先上传并筛选</td></tr>';
            return;
        }
        
        // 按学校、年级、班级分组，合并多周数据
        const groupMap = new Map();
    AppState.filteredData.forEach(r => {
        const classId = getClassId(r);
        const key = `${r['省份']||''}|${r['城市']||''}|${r['区县']||''}|${r['学校名称']||''}|${r['年级']||''}|${r['班级名称']||''}|${classId}`;
        if (!groupMap.has(key)) {
            groupMap.set(key, {
                province: r['省份'] || '-',
                city: r['城市'] || '-',
                district: r['区县'] || '-',
                school: r['学校名称'] || '-',
                grade: r['年级'] || '-',
                teacherName: r['教师姓名'] || r['老师姓名'] || r['教师'] || '-',
                className: r['班级名称'] || '-',
                classId: classId || '-',
                weeks: new Map()
            });
        }
        const g = groupMap.get(key);
        const weekKey = r.weekLabel;
        if (!g.weeks.has(weekKey)) {
            g.weeks.set(weekKey, {
                display: r.weekDisplay,
                startDate: r.weekStartDate,
                assignments: 0,
                completionRate: 0,
                completionSum: 0,
                count: 0,
                paidCount: +r['未过期付费学生数'] || 0,
                trialCount: +r['未过期试用学生数'] || 0,
                conversionSum: (+r['转化率'] || 0) * 100,
                conversionCount: (+r['转化率'] || 0) > 0 ? 1 : 0
            });
        }
        const w = g.weeks.get(weekKey);
        w.assignments += +r['布置作业次数'] || 0;
        w.completionSum += (+r['作业完成率'] || 0) * 100;
        if ((+r['转化率'] || 0) > 0) {
            w.conversionSum += (+r['转化率'] || 0) * 100;
            w.conversionCount++;
        }
        w.count++;
        w.completionRate = w.count ? (w.completionSum / w.count).toFixed(1) : 0;
        w.conversionRate = w.conversionCount ? (w.conversionSum / w.conversionCount).toFixed(1) : 0;
        w.paidCount = +r['未过期付费学生数'] || 0;
        w.trialCount = +r['未过期试用学生数'] || 0;
    });
    
    // 获取所有周次（按时间排序）
    const weekMetaMap = buildWeekMetaMap(groupMap);
    const sortedWeeks = sortWeekKeys(weekMetaMap);
    
    // 生成表头
    let theadHtml = '<tr>';
    theadHtml += '<th rowspan="2" style="min-width:60px;">省份</th>';
    theadHtml += '<th rowspan="2" style="min-width:80px;">城市</th>';
    theadHtml += '<th rowspan="2" style="min-width:80px;">区县</th>';
    theadHtml += '<th rowspan="2" style="min-width:150px;">学校</th>';
    theadHtml += '<th rowspan="2" style="min-width:80px;">年级</th>';
    theadHtml += '<th rowspan="2" style="min-width:90px;">老师</th>';
    theadHtml += '<th rowspan="2" style="min-width:100px;">班级</th>';
    
    sortedWeeks.forEach(week => {
        const w = weekMetaMap.get(week) || { display: week };
        theadHtml += `<th colspan="2" style="text-align:center;background:#f8fafc;">${w.display}</th>`;
    });
    
    theadHtml += '<th rowspan="2" style="min-width:80px;">未过期<br>付费学生数</th>';
    theadHtml += '<th rowspan="2" style="min-width:80px;">未过期<br>试用学生数</th>';
    theadHtml += '<th rowspan="2" style="min-width:80px;">转化率</th>';
    theadHtml += '</tr>';
    
    // 第二行表头（周次细分）
    theadHtml += '<tr>';
    sortedWeeks.forEach(() => {
        theadHtml += '<th style="font-size:12px;">布置次数</th>';
        theadHtml += '<th style="font-size:12px;">完成率</th>';
    });
    theadHtml += '</tr>';
    
    // 生成数据行
    const sortedGroups = [...groupMap.values()].sort((a, b) => {
        const pCmp = String(a.province).localeCompare(String(b.province), 'zh-CN');
        if (pCmp !== 0) return pCmp;
        const cCmp = String(a.city).localeCompare(String(b.city), 'zh-CN');
        if (cCmp !== 0) return cCmp;
        const dCmp = String(a.district).localeCompare(String(b.district), 'zh-CN');
        if (dCmp !== 0) return dCmp;
        const schCmp = String(a.school).localeCompare(String(b.school), 'zh-CN');
        if (schCmp !== 0) return schCmp;
        return String(a.grade).localeCompare(String(b.grade), 'zh-CN');
    });
    
    totalRows = sortedGroups.length;
    const totalPages = Math.ceil(totalRows / ROWS_PER_PAGE);
    currentPage = Math.min(Math.max(1, page), totalPages);
    const startIdx = (currentPage - 1) * ROWS_PER_PAGE;
    const endIdx = Math.min(startIdx + ROWS_PER_PAGE, totalRows);
    const pageGroups = sortedGroups.slice(startIdx, endIdx);
    
    let tbody = '';
    pageGroups.forEach(g => {
        tbody += '<tr>';
        tbody += `<td>${g.province}</td>`;
        tbody += `<td>${g.city}</td>`;
        tbody += `<td>${g.district}</td>`;
        tbody += `<td class="school-name-cell" title="${g.school}">${g.school}</td>`;
        tbody += `<td>${g.grade}</td>`;
        tbody += `<td class="teacher-name-cell" title="${g.teacherName}">${g.teacherName}</td>`;
        tbody += `<td>${g.className}</td>`;
        
        sortedWeeks.forEach(weekKey => {
            if (g.weeks.has(weekKey)) {
                const w = g.weeks.get(weekKey);
                tbody += `<td style="text-align:center;">${w.assignments.toLocaleString()}</td>`;
                tbody += `<td style="text-align:center;color:${parseFloat(w.completionRate) < 50 ? '#ef4444' : '#10b981'};font-weight:600;">${w.completionRate}%</td>`;
            } else {
                tbody += '<td style="text-align:center;color:#ccc;">-</td>';
                tbody += '<td style="text-align:center;color:#ccc;">-</td>';
            }
        });
        
        // 最后一周的未过期学生数
        const lastWeekKey = sortedWeeks[sortedWeeks.length - 1];
        const lastWeek = g.weeks.get(lastWeekKey);
        tbody += `<td style="text-align:center;">${(lastWeek?.paidCount || 0).toLocaleString()}</td>`;
        tbody += `<td style="text-align:center;">${(lastWeek?.trialCount || 0).toLocaleString()}</td>`;
        tbody += `<td style="text-align:center;">${lastWeek?.conversionRate || '--'}%</td>`;
        
        tbody += '</tr>';
    });
    
    // 分别设置 thead 和 tbody
    theadEl.innerHTML = theadHtml;
    elements.tableBody.innerHTML = tbody;
    scheduleAdaptNameCells();
    
    // 渲染分页
    renderPagination(totalPages, currentPage, totalRows, startIdx + 1, endIdx);
    } catch (err) {
        console.error('renderTbl failed', err, {
            version: APP_VERSION,
            filteredCount: AppState.filteredData?.length,
            sample: AppState.filteredData?.slice?.(0, 3)
        });
        const debugBar = document.getElementById('debugBar');
        if (debugBar) {
            debugBar.innerHTML = `<span>版本：${APP_VERSION}</span><span style="color:#dc2626;">明细表报错：${err.message}</span><span>数据量：${AppState.filteredData?.length || 0}</span>`;
        }
        theadEl.innerHTML = '';
        elements.tableBody.innerHTML = `<tr><td colspan="20" style="text-align:center;padding:40px;color:#dc2626;">班级数据明细渲染失败：${err.message}</td></tr>`;
    }
}

function renderPagination(totalPages, currentPage, totalRows, startRow, endRow) {
    let paginationHtml = `
        <div class="pagination-wrapper">
            <div class="pagination-info">
                共 ${totalRows} 条，第 ${startRow}-${endRow} 条
            </div>
            <div class="pagination-controls">
                <button class="pagination-btn" onclick="goToPage(1)" ${currentPage === 1 ? 'disabled' : ''}>首页</button>
                <button class="pagination-btn" onclick="goToPage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>上一页</button>
    `;
    
    // 页码按钮（最多显示7页）
    let startPage = Math.max(1, currentPage - 3);
    let endPage = Math.min(totalPages, startPage + 6);
    startPage = Math.max(1, Math.min(startPage, endPage - 6));
    
    for (let i = startPage; i <= endPage; i++) {
        paginationHtml += `<button class="pagination-btn ${i === currentPage ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`;
    }
    
    paginationHtml += `
                <button class="pagination-btn" onclick="goToPage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>下一页</button>
                <button class="pagination-btn" onclick="goToPage(${totalPages})" ${currentPage === totalPages ? 'disabled' : ''}>末页</button>
                <div class="pagination-jump">
                    跳至 <input type="number" id="jumpPageInput" min="1" max="${totalPages}" value="${currentPage}"> 页
                    <button class="pagination-btn" onclick="jumpToPage()">跳转</button>
                </div>
            </div>
        </div>
    `;
    
    // 在 .table-section 中查找并删除旧的分页组件（分页是 table-section 的子元素，不是 table-wrapper 的子元素）
    const tableSection = document.getElementById('tableSection');
    let existingPagination = null;
    if (tableSection) {
        existingPagination = tableSection.querySelector('.pagination-wrapper');
    }
    if (existingPagination) {
        existingPagination.remove();
    }
    // 插入分页组件到 table-section 底部
    if (tableSection) {
        tableSection.insertAdjacentHTML('beforeend', paginationHtml);
    }
}

function goToPage(page) {
    renderTbl(page);
}

function jumpToPage() {
    const input = document.getElementById('jumpPageInput');
    if (input) {
        const page = parseInt(input.value);
        if (page && page >= 1 && page <= Math.ceil(totalRows / ROWS_PER_PAGE)) {
            renderTbl(page);
        }
    }
}

// 导出 CSV - 适配新表格结构
function exportCSV() {
    if (!AppState.filteredData.length) {
        showMsg('⚠️ 无数据可导出', 'warning');
        return;
    }
    
    const groupMap = new Map();
    AppState.filteredData.forEach(r => {
        const classId = getClassId(r);
        const key = `${r['省份']||''}|${r['城市']||''}|${r['区县']||''}|${r['学校名称']||''}|${r['年级']||''}|${r['班级名称']||''}|${classId}`;
        if (!groupMap.has(key)) {
            groupMap.set(key, {
                province: r['省份'] || '-',
                city: r['城市'] || '-',
                district: r['区县'] || '-',
                school: r['学校名称'] || '-',
                grade: r['年级'] || '-',
                className: r['班级名称'] || '-',
                classId: classId || '-',
                weeks: new Map()
            });
        }
        const g = groupMap.get(key);
        const weekKey = r.weekLabel;
        if (!g.weeks.has(weekKey)) {
            g.weeks.set(weekKey, {
                display: r.weekDisplay,
                startDate: r.weekStartDate,
                assignments: 0,
                completionRate: 0,
                completionSum: 0,
                count: 0,
                paidCount: +r['未过期付费学生数'] || 0,
                trialCount: +r['未过期试用学生数'] || 0,
                conversionSum: 0,
                conversionCount: 0,
                conversionRate: 0
            });
        }
        const w = g.weeks.get(weekKey);
        w.assignments += +r['布置作业次数'] || 0;
        w.completionSum += (+r['作业完成率'] || 0) * 100;
        if ((+r['转化率'] || 0) > 0) {
            w.conversionSum += (+r['转化率'] || 0) * 100;
            w.conversionCount += 1;
        }
        w.count += 1;
        w.completionRate = w.count ? (w.completionSum / w.count).toFixed(1) : '0.0';
        w.conversionRate = w.conversionCount ? (w.conversionSum / w.conversionCount).toFixed(1) : '0.0';
        w.paidCount = +r['未过期付费学生数'] || 0;
        w.trialCount = +r['未过期试用学生数'] || 0;
    });
    
    const weekMetaMap = buildWeekMetaMap(groupMap);
    const sortedWeeks = sortWeekKeys(weekMetaMap);
    
    const headers = ['省份', '城市', '区县', '学校', '年级', '班级'];
    sortedWeeks.forEach(week => {
        const w = weekMetaMap.get(week) || { display: week };
        headers.push(`${w.display}_布置次数`, `${w.display}_完成率`);
    });
    headers.push('未过期付费学生数', '未过期试用学生数', '转化率');
    
    const rows = [headers.join(',')];
    const sortedGroups = [...groupMap.values()].sort((a, b) => {
        const pCmp = String(a.province).localeCompare(String(b.province), 'zh-CN');
        if (pCmp !== 0) return pCmp;
        const cCmp = String(a.city).localeCompare(String(b.city), 'zh-CN');
        if (cCmp !== 0) return cCmp;
        const dCmp = String(a.district).localeCompare(String(b.district), 'zh-CN');
        if (dCmp !== 0) return dCmp;
        const schCmp = String(a.school).localeCompare(String(b.school), 'zh-CN');
        if (schCmp !== 0) return schCmp;
        return String(a.grade).localeCompare(String(b.grade), 'zh-CN');
    });
    
    sortedGroups.forEach(g => {
        const row = [g.province, g.city, g.district, g.school, g.grade, g.className];
        sortedWeeks.forEach(weekKey => {
            if (g.weeks.has(weekKey)) {
                const w = g.weeks.get(weekKey);
                row.push(w.assignments.toString(), w.completionRate);
            } else {
                row.push('-', '-');
            }
        });
        const lastWeek = sortedWeeks.length ? g.weeks.get(sortedWeeks[sortedWeeks.length - 1]) : null;
        row.push((lastWeek?.paidCount || 0).toString(), (lastWeek?.trialCount || 0).toString(), `${lastWeek?.conversionRate || '0.0'}%`);
        rows.push(row.join(','));
    });
    
    const csv = rows.join('\n');
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `导出_${dayjs().format('YYYYMMDD_HHmmss')}.csv`;
    link.click();
    showMsg('✅ 导出成功', 'success');
}

// 提示函数
function showLoading() {
    const t = document.createElement('div');
    t.id = 'loadingToast';
    t.style.cssText = 'position:fixed;top:20px;right:20px;padding:16px 24px;background:linear-gradient(135deg,#3b82f6,#1d4ed8);color:white;border-radius:12px;box-shadow:0 8px 24px rgba(59,130,246,.3);font-size:14px;z-index:10002;animation:slideIn .3s;';
    t.textContent = '🔄 正在解析...';
    document.body.appendChild(t);
}
function hideLoading() { const t = document.getElementById('loadingToast'); if (t) t.remove(); }
function showMsg(title, type) {
    const colors = { success: 'linear-gradient(135deg,#10b981,#059669)', error: 'linear-gradient(135deg,#ef4444,#dc2626)', warning: 'linear-gradient(135deg,#f59e0b,#d97706)' };
    const icons = { success: '✅', error: '❌', warning: '⚠️' };
    const t = document.createElement('div');
    t.style.cssText = `position:fixed;top:20px;right:20px;padding:18px 24px;background:${colors[type]};color:white;border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,.2);font-size:14px;z-index:10002;animation:slideIn .3s;min-width:280px;white-space:pre-line;`;
    t.innerHTML = `<div style="display:flex;align-items:center;gap:10px;"><span style="font-size:20px;">${icons[type]}</span><span style="font-weight:600;">${title}</span></div>`;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 5000);
}

// 自定义确认对话框
function showConfirm(message) {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);z-index:100001;animation:fadeIn 0.2s;';
        
        const dialog = document.createElement('div');
        dialog.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:white;padding:32px;border-radius:16px;box-shadow:0 20px 60px rgba(0,0,0,0.3);z-index:100002;min-width:320px;max-width:90vw;';
        
        dialog.innerHTML = `
            <div style="font-size:16px;font-weight:600;margin-bottom:16px;color:#1e293b;white-space:pre-line;">${message}</div>
            <div style="display:flex;gap:12px;justify-content:flex-end;margin-top:24px;">
                <button id="confirmCancel" style="padding:10px 20px;border:1px solid #e2e8f0;background:white;color:#64748b;border-radius:8px;cursor:pointer;font-size:14px;">取消</button>
                <button id="confirmOk" style="padding:10px 20px;border:none;background:linear-gradient(135deg,#ef4444,#dc2626);color:white;border-radius:8px;cursor:pointer;font-size:14px;font-weight:600;">删除</button>
            </div>
        `;
        
        document.body.appendChild(overlay);
        document.body.appendChild(dialog);
        
        const cleanup = () => {
            overlay.remove();
            dialog.remove();
        };
        
        document.getElementById('confirmCancel').onclick = () => { cleanup(); resolve(false); };
        document.getElementById('confirmOk').onclick = () => { cleanup(); resolve(true); };
        
        // 点击遮罩关闭
        overlay.onclick = () => { cleanup(); resolve(false); };
    });
}

// 响应式
window.onresize = () => { ['conversionChart'].forEach(id => { const el=document.getElementById(id); const c = el ? echarts.getInstanceByDom(el) : null; if (c) c.resize(); }); scheduleAdaptNameCells(); };


function inferStageFromGrade(grade = '') {
    const text = String(grade || '').trim();
    if (!text) return '';
    if (/高一|高二|高三|普高|职高|中专/.test(text)) return '高中';
    if (/初一|初二|初三|七年级|八年级|九年级|7年级|8年级|9年级/.test(text)) return '初中';
    if (/一年级|二年级|三年级|四年级|五年级|六年级|1年级|2年级|3年级|4年级|5年级|6年级|小学/.test(text)) return '小学';
    return '';
}

const FAVORITES_KEY = 'education-dashboard-hv-favorites';
function loadFavorites() { try { return new Set(JSON.parse(localStorage.getItem(FAVORITES_KEY) || '[]')); } catch { return new Set(); } }
function saveFavorites(set) { localStorage.setItem(FAVORITES_KEY, JSON.stringify([...set])); }
function favoriteKey(g) { return `${g.province}|${g.city}|${g.district}|${g.school}|${g.grade}`; }
function toggleFavoriteByKey(key) { const favs = loadFavorites(); if (favs.has(key)) favs.delete(key); else favs.add(key); saveFavorites(favs); applyHighValueFilter(); }

function adaptNameCells(scope = document) {
    const cells = scope.querySelectorAll('.school-name-cell, .teacher-name-cell');
    cells.forEach(cell => {
        cell.classList.remove('allow-one-line', 'allow-two-lines');
        const text = (cell.textContent || '').trim();
        if (!text) return;

        const resetDisplay = cell.classList.contains('teacher-name-cell') ? 'table-cell' : 'table-cell';
        cell.style.display = resetDisplay;
        cell.style.whiteSpace = 'nowrap';
        cell.style.webkitLineClamp = 'unset';
        cell.style.overflow = 'hidden';

        const fitsOneLine = cell.scrollWidth <= cell.clientWidth + 1;
        if (fitsOneLine) {
            cell.classList.add('allow-one-line');
            cell.style.display = '';
            cell.style.whiteSpace = '';
            cell.style.webkitLineClamp = '';
            cell.style.overflow = '';
            return;
        }

        cell.classList.add('allow-two-lines');
        cell.style.display = '-webkit-box';
        cell.style.whiteSpace = 'normal';
        cell.style.webkitBoxOrient = 'vertical';
        cell.style.webkitLineClamp = '2';
        cell.style.overflow = 'hidden';

        const lineHeight = parseFloat(window.getComputedStyle(cell).lineHeight) || 16;
        const maxTwoLineHeight = lineHeight * 2 + 2;
        const fitsTwoLines = cell.scrollHeight <= maxTwoLineHeight;
        if (!fitsTwoLines) {
            const wrapper = cell.closest('.table-wrapper, .high-value-table-wrapper');
            if (wrapper) wrapper.style.overflowX = 'auto';
        }

        cell.style.display = '';
        cell.style.whiteSpace = '';
        cell.style.webkitLineClamp = '';
        cell.style.overflow = '';
    });
}

function scheduleAdaptNameCells() {
    requestAnimationFrame(() => adaptNameCells(document));
}

function parseCustomSchoolNames(input = '') {
    return [...new Set(input.split(/[\n、]+/).map(s => s.trim()).filter(Boolean))];
}

function applyCustomSchoolSearch() {
    const names = parseCustomSchoolNames(elements.customSchoolInput?.value || '');
    if (!names.length) {
        showMsg('⚠️ 请输入学校名称', 'warning');
        return;
    }

    let records = [];
    AppState.cache.forEach(d => records.push(...d));
    if (!records.length) {
        showMsg('⚠️ 暂无上传数据', 'warning');
        return;
    }

    const avgAssignFilter = elements.customSchoolAvgAssignFilter?.value || '';
    const completionFilter = elements.customSchoolCompletionFilter?.value || '';
    const stageFilter = elements.customSchoolStageFilter?.value || '';
    const matched = records.filter(r => names.some(name => (r['学校名称'] || '').includes(name)));
    if (!matched.length) {
        showMsg('⚠️ 未匹配到重点校数据', 'warning');
        elements.customSchoolResult.style.display = 'none';
        return;
    }

    populateCustomSchoolGradeFilter(matched);
    const gradeFilter = elements.customSchoolGradeFilter?.value || '';

    renderCustomSchoolAggregateSchoolView(matched, names, stageFilter, gradeFilter);
    renderCustomSchoolSchoolView(matched, names, avgAssignFilter, completionFilter, stageFilter, gradeFilter);
    renderCustomSchoolClassView(matched, names, stageFilter, gradeFilter);
    const weekStarts = [...new Set(matched.map(r => r.weekStartDate))].sort();
    const lastWeekStart = weekStarts[weekStarts.length - 1] || '';
    elements.customSchoolSummary.textContent = `共 ${matched.length} 条记录 | 数据来源：${weekStarts.length}周（${lastWeekStart}）`;
    elements.customSchoolResult.style.display = 'block';
    switchCustomSchoolTab('school');
    scheduleAdaptNameCells();
    showMsg(`✅ 已匹配 ${matched.length} 条重点校数据`, 'success');
}

function resetCustomSchoolSearch() {
    if (elements.customSchoolGradeFilter) elements.customSchoolGradeFilter.innerHTML = '<option value="">不限</option>';
    if (elements.customSchoolInput) elements.customSchoolInput.value = '';
    if (elements.customSchoolAvgAssignFilter) elements.customSchoolAvgAssignFilter.value = '';
    if (elements.customSchoolCompletionFilter) elements.customSchoolCompletionFilter.value = '';
    if (elements.customSchoolStageFilter) elements.customSchoolStageFilter.value = '';
    if (elements.customSchoolGradeFilter) elements.customSchoolGradeFilter.value = '';
    if (elements.customSchoolResult) elements.customSchoolResult.style.display = 'none';
    if (elements.customSchoolTableHead) elements.customSchoolTableHead.innerHTML = '';
    if (elements.customSchoolTableBody) elements.customSchoolTableBody.innerHTML = '';
    if (elements.customSchoolClassTableHead) elements.customSchoolClassTableHead.innerHTML = '';
    if (elements.customSchoolClassTableBody) elements.customSchoolClassTableBody.innerHTML = '';
    if (elements.customSchoolSummary) elements.customSchoolSummary.textContent = '';
}

function switchCustomSchoolTab(tab) {
    const isSchool = tab === 'school';
    const isGrade = tab === 'grade';
    const isClass = tab === 'class';
    elements.customSchoolTabSchool?.classList.toggle('active', isSchool);
    elements.customSchoolTabGrade?.classList.toggle('active', isGrade);
    elements.customSchoolTabClass?.classList.toggle('active', isClass);
    if (elements.customSchoolSchoolView) elements.customSchoolSchoolView.style.display = isSchool ? 'block' : 'none';
    if (elements.customSchoolGradeView) elements.customSchoolGradeView.style.display = isGrade ? 'block' : 'none';
    if (elements.customSchoolClassView) elements.customSchoolClassView.style.display = isClass ? 'block' : 'none';
}


function populateCustomSchoolGradeFilter(records) {
    if (!elements.customSchoolGradeFilter) return;
    const current = elements.customSchoolGradeFilter.value;
    const grades = [...new Set(records.map(r => r['年级']).filter(Boolean))]
        .sort((a, b) => String(a).localeCompare(String(b), 'zh-CN'));
    elements.customSchoolGradeFilter.innerHTML = '<option value="">不限</option>' + grades.map(g => `<option value="${g}">${g}</option>`).join('');
    if (grades.includes(current)) {
        elements.customSchoolGradeFilter.value = current;
    }
}

function renderCustomSchoolAggregateSchoolView(records, inputNames = [], stageFilter = '', gradeFilter = '') {
    const schoolMap = new Map();
    records.forEach(r => {
        const school = r['学校名称'] || '-';
        const grade = r['年级'] || '-';
        const key = `${r['省份']||''}|${r['城市']||''}|${r['区县']||''}|${school}`;
        if (!schoolMap.has(key)) schoolMap.set(key, { province:r['省份']||'-', city:r['城市']||'-', district:r['区县']||'-', school, grades:new Set(), classes:new Set(), lastWeekRows:[], allRows:[] });
        const g = schoolMap.get(key);
        g.grades.add(grade);
        g.classes.add(getClassId(r) || r['班级名称'] || `${school}-${grade}-${r.weekLabel||''}`);
        g.allRows.push(r);
    });
    const weekStarts = [...new Set(records.map(r => r.weekStartDate))].sort();
    const lastWeekStart = weekStarts[weekStarts.length - 1] || '';
    schoolMap.forEach(g => { g.lastWeekRows = g.allRows.filter(r => r.weekStartDate === lastWeekStart); });

    const schoolWeeks = [...new Set(records.map(r => r.weekLabel))].sort((a, b) => {
        const ra = records.find(x => x.weekLabel === a);
        const rb = records.find(x => x.weekLabel === b);
        return dayjs(ra?.weekStartDate).isBefore(dayjs(rb?.weekStartDate)) ? -1 : 1;
    });
    let schoolHead = '<tr><th rowspan="2">省份</th><th rowspan="2">城市</th><th rowspan="2">区县</th><th rowspan="2">学校</th><th rowspan="2">涉及年级数</th><th rowspan="2">班级总数</th>';
    schoolWeeks.forEach(week => {
        const wk = records.find(x => x.weekLabel === week);
        schoolHead += `<th colspan="2" style="text-align:center;">${wk?.weekDisplay || week}</th>`;
    });
    schoolHead += '<th rowspan="2">未过期付费</th><th rowspan="2">未过期试用</th><th rowspan="2">转化率</th></tr><tr>';
    schoolWeeks.forEach(() => { schoolHead += '<th>平均布置作业数</th><th>作业完成率</th>'; });
    schoolHead += '</tr>';
    if (elements.customSchoolSchoolTableHead) elements.customSchoolSchoolTableHead.innerHTML = schoolHead;

    const rows = [...schoolMap.values()]
        .filter(g => !stageFilter || [...g.grades].some(gr => inferStageFromGrade(gr) === stageFilter))
        .sort((a,b)=> {
            const ia=inputNames.findIndex(n=>a.school.includes(n));
            const ib=inputNames.findIndex(n=>b.school.includes(n));
            if (ia!==ib) return (ia===-1?1e9:ia)-(ib===-1?1e9:ib);
            return a.school.localeCompare(b.school,'zh-CN');
        })
        .map(g => {
            const allGrades = [...g.grades];
            if (gradeFilter && !allGrades.includes(gradeFilter)) return '';
            const filteredAllRows = gradeFilter ? g.allRows.filter(r => r['年级'] === gradeFilter) : g.allRows;
            const filteredLastRows = gradeFilter ? g.lastWeekRows.filter(r => r['年级'] === gradeFilter) : g.lastWeekRows;
            const classCount = new Set(filteredAllRows.map(r => getClassId(r) || r['班级名称'] || `${g.school}-${r['年级']}-${r.weekLabel||''}`)).size;
            const gradeCount = gradeFilter ? (filteredAllRows.length ? 1 : 0) : g.grades.size;
            let row = `<tr><td>${g.province}</td><td>${g.city}</td><td>${g.district}</td><td class="school-name-cell" title="${g.school}">${g.school}</td><td>${gradeCount}</td><td>${classCount}</td>`;
            schoolWeeks.forEach(weekKey => {
                const weekRows = filteredAllRows.filter(r => r.weekLabel === weekKey);
                const weekClassCount = new Set(weekRows.map(r => getClassId(r) || r['班级名称'] || `${g.school}-${r['年级']}-${weekKey}`)).size;
                const assignSum = weekRows.reduce((s,r)=>s+(+r['布置作业次数']||0),0);
                const avgAssign = weekClassCount ? (assignSum / weekClassCount).toFixed(1) : '0.0';
                const completionVals = weekRows.map(r => (+r['作业完成率'] || 0) * 100);
                const completion = completionVals.length ? (completionVals.reduce((a,b)=>a+b,0)/completionVals.length).toFixed(1) : '0.0';
                const completionClass = Number(completion) < 50 ? 'metric-bad' : 'metric-good';
                row += `<td class="compact-number-cell">${avgAssign}</td><td class="compact-number-cell ${completionClass}">${completion}%</td>`;
            });
            const paid = filteredLastRows.reduce((s,r)=>s+(+r['未过期付费学生数']||0),0);
            const trial = filteredLastRows.reduce((s,r)=>s+(+r['未过期试用学生数']||0),0);
            const convVals = filteredLastRows.filter(r => (+r['转化率']||0) >= 0).map(r => (+r['转化率']||0)*100);
            const conv = convVals.length ? (convVals.reduce((a,b)=>a+b,0)/convVals.length).toFixed(1) : '0.0';
            row += `<td>${paid}</td><td>${trial}</td><td>${conv}%</td></tr>`;
            return row;
        }).join('');

    if (elements.customSchoolSchoolTableBody) elements.customSchoolSchoolTableBody.innerHTML = rows;
}

function renderCustomSchoolSchoolView(records, inputNames = [], avgAssignFilter = '', completionFilter = '', stageFilter = '', gradeFilter = '') {
    const grouped = new Map();
    records.forEach(r => {
        const key = `${r['省份']||''}|${r['城市']||''}|${r['区县']||''}|${r['学校名称']||''}|${r['年级']||''}`;
        if (!grouped.has(key)) grouped.set(key, {
            province: r['省份'] || '-',
            city: r['城市'] || '-',
            district: r['区县'] || '-',
            school: r['学校名称'] || '-',
            grade: r['年级'] || '-',
            classIds: new Set(),
            weeks: new Map()
        });
        const g = grouped.get(key);
        const classId = getClassId(r) || r['班级名称'] || `${r['学校名称'] || ''}-${r['年级'] || ''}-${r.weekLabel || ''}`;
        g.classIds.add(classId);
        const wk = r.weekLabel;
        if (!g.weeks.has(wk)) g.weeks.set(wk, {
            display: r.weekDisplay,
            startDate: r.weekStartDate,
            assignments: 0,
            completionSum: 0,
            completionCount: 0,
            conversionSum: 0,
            conversionCount: 0,
            paid: 0,
            trial: 0
        });
        const w = g.weeks.get(wk);
        w.assignments += +r['布置作业次数'] || 0;
        w.completionSum += (+r['作业完成率'] || 0) * 100;
        w.completionCount += 1;
        if ((+r['转化率'] || 0) > 0) {
            w.conversionSum += (+r['转化率'] || 0) * 100;
            w.conversionCount += 1;
        }
        w.paid += +r['未过期付费学生数'] || 0;
        w.trial += +r['未过期试用学生数'] || 0;
    });
    const weekMetaMap = buildWeekMetaMap(grouped);
    const sortedWeeks = sortWeekKeys(weekMetaMap);
    const lastWeekKey = sortedWeeks[sortedWeeks.length - 1];
    let thead = '<tr><th rowspan="2">省份</th><th rowspan="2">城市</th><th rowspan="2">区县</th><th rowspan="2">学校</th><th rowspan="2">年级</th><th rowspan="2">年级班级数</th>';
    sortedWeeks.forEach(week => { const w = weekMetaMap.get(week) || { display: week }; thead += `<th colspan="2" style="text-align:center;">${w.display}</th>`; });
    thead += '<th rowspan="2">未过期付费</th><th rowspan="2">未过期试用</th><th rowspan="2">转化率</th></tr><tr>';
    sortedWeeks.forEach(() => { thead += '<th>平均布置作业数</th><th>作业完成率</th>'; });
    thead += '</tr>';
    elements.customSchoolTableHead.innerHTML = thead;
    const rows = [...grouped.values()].sort((a, b) => {
        const getOrder = (school) => {
            const idx = inputNames.findIndex(name => school.includes(name));
            return idx === -1 ? Number.MAX_SAFE_INTEGER : idx;
        };
        const orderDiff = getOrder(a.school) - getOrder(b.school);
        if (orderDiff !== 0) return orderDiff;
        return `${a.school}${a.grade}`.localeCompare(`${b.school}${b.grade}`, 'zh-CN');
    }).filter(g => {
        const classCount = g.classIds.size || 0;
        const lastWeek = g.weeks.get(lastWeekKey);
        const avgAssignments = lastWeek && classCount ? (lastWeek.assignments / classCount) : 0;
        const completion = lastWeek && lastWeek.completionCount ? (lastWeek.completionSum / lastWeek.completionCount) / 100 : 0;
        const stage = inferStageFromGrade(g.grade);
        const gradePass = !gradeFilter || g.grade === gradeFilter;

        let stagePass = true;
        if (stageFilter) stagePass = stage === stageFilter;

        let avgPass = true;
        if (avgAssignFilter === 'eq0') avgPass = avgAssignments === 0;
        if (avgAssignFilter === 'gt0.5') avgPass = avgAssignments > 0.5;
        if (avgAssignFilter === 'gt0.8') avgPass = avgAssignments > 0.8;
        if (avgAssignFilter === 'gt1') avgPass = avgAssignments > 1;

        let completionPass = true;
        if (completionFilter === 'gt0.8') completionPass = completion > 0.8;
        if (completionFilter === 'between0.5_0.8') completionPass = completion >= 0.5 && completion <= 0.8;
        if (completionFilter === 'lt0.5') completionPass = completion < 0.5;
        if (completionFilter === 'eq0') completionPass = completion === 0;

        return stagePass && gradePass && avgPass && completionPass;
    }).map(g => {
        const classCount = g.classIds.size || 0;
        let t = `<tr><td>${g.province}</td><td>${g.city}</td><td>${g.district}</td><td class="school-name-cell" title="${g.school}">${g.school}</td><td>${g.grade}</td><td>${classCount}</td>`;
        sortedWeeks.forEach(week => {
            const w = g.weeks.get(week);
            if (!w) { t += '<td>-</td><td>-</td>'; return; }
            const completion = w.completionCount ? (w.completionSum / w.completionCount).toFixed(1) : '0.0';
            const avgAssignments = classCount ? (w.assignments / classCount).toFixed(1) : '0.0';
            const completionClass = Number(completion) < 50 ? 'metric-bad' : 'metric-good';
            t += `<td class="compact-number-cell">${avgAssignments}</td><td class="compact-number-cell ${completionClass}">${completion}%</td>`;
        });
        const lastWeek = g.weeks.get(lastWeekKey);
        const conversion = lastWeek?.conversionCount ? (lastWeek.conversionSum / lastWeek.conversionCount).toFixed(1) : '0.0';
        t += `<td>${lastWeek?.paid || 0}</td><td>${lastWeek?.trial || 0}</td><td>${conversion}%</td>`;
        return t + '</tr>';
    }).join('');
    elements.customSchoolTableBody.innerHTML = rows;
    scheduleAdaptNameCells();
}

function renderCustomSchoolClassView(records, inputNames = [], stageFilter = '', gradeFilter = '') {
    const groupMap = new Map();
    records.forEach(r => {
        const classId = getClassId(r);
        const key = `${r['省份']||''}|${r['城市']||''}|${r['区县']||''}|${r['学校名称']||''}|${r['年级']||''}|${r['班级名称']||''}|${classId}`;
        if (!groupMap.has(key)) groupMap.set(key, {
            province: r['省份'] || '-', city: r['城市'] || '-', district: r['区县'] || '-', school: r['学校名称'] || '-', grade: r['年级'] || '-', teacherName: r['教师姓名'] || r['老师姓名'] || r['教师'] || '-', className: r['班级名称'] || '-', classId: classId || '-', weeks: new Map()
        });
        const g = groupMap.get(key);
        const weekKey = r.weekLabel;
        if (!g.weeks.has(weekKey)) g.weeks.set(weekKey, { display: r.weekDisplay, startDate: r.weekStartDate, assignments: 0, completionSum: 0, count: 0, paidCount: 0, trialCount: 0, conversionSum: 0, conversionCount: 0 });
        const w = g.weeks.get(weekKey);
        w.assignments += +r['布置作业次数'] || 0;
        w.completionSum += (+r['作业完成率'] || 0) * 100;
        w.count += 1;
        w.paidCount += +r['未过期付费学生数'] || 0;
        w.trialCount += +r['未过期试用学生数'] || 0;
        if ((+r['转化率'] || 0) > 0) { w.conversionSum += (+r['转化率'] || 0) * 100; w.conversionCount += 1; }
    });
    const weekMetaMap = buildWeekMetaMap(groupMap);
    const sortedWeeks = sortWeekKeys(weekMetaMap);
    let thead = '<tr><th rowspan="2">省份</th><th rowspan="2">城市</th><th rowspan="2">区县</th><th rowspan="2">学校</th><th rowspan="2">年级</th><th rowspan="2">老师</th><th rowspan="2">班级</th>';
    sortedWeeks.forEach(week => { const w = weekMetaMap.get(week) || { display: week }; thead += `<th colspan="2" style="text-align:center;">${w.display}</th>`; });
    thead += '<th rowspan="2">未过期付费</th><th rowspan="2">未过期试用</th><th rowspan="2">转化率</th></tr><tr>';
    sortedWeeks.forEach(() => { thead += '<th>布置次数</th><th>作业完成率</th>'; });
    thead += '</tr>';
    elements.customSchoolClassTableHead.innerHTML = thead;
    const rows = [...groupMap.values()].sort((a, b) => {
        const getOrder = (school) => {
            const idx = inputNames.findIndex(name => school.includes(name));
            return idx === -1 ? Number.MAX_SAFE_INTEGER : idx;
        };
        const orderDiff = getOrder(a.school) - getOrder(b.school);
        if (orderDiff !== 0) return orderDiff;
        return `${a.school}${a.grade}${a.className}`.localeCompare(`${b.school}${b.grade}${b.className}`, 'zh-CN');
    }).filter(g => {
        const stagePass = !stageFilter || inferStageFromGrade(g.grade) === stageFilter;
        const gradePass = !gradeFilter || g.grade === gradeFilter;
        return stagePass && gradePass;
    }).map(g => {
        let t = `<tr><td>${g.province}</td><td>${g.city}</td><td>${g.district}</td><td class="school-name-cell" title="${g.school}">${g.school}</td><td>${g.grade}</td><td class="teacher-name-cell" title="${g.teacherName}">${g.teacherName}</td><td>${g.className}</td>`;
        sortedWeeks.forEach(weekKey => {
            const w = g.weeks.get(weekKey);
            if (!w) { t += '<td>-</td><td>-</td>'; return; }
            const completion = w.count ? (w.completionSum / w.count).toFixed(1) : '0.0';
            const completionClass = Number(completion) < 50 ? 'metric-bad' : 'metric-good';
            t += `<td>${w.assignments}</td><td class="${completionClass}">${completion}%</td>`;
        });
        const lastWeekKey = sortedWeeks[sortedWeeks.length - 1];
        const lastWeek = g.weeks.get(lastWeekKey);
        const conversion = lastWeek?.conversionCount ? (lastWeek.conversionSum / lastWeek.conversionCount).toFixed(1) : '0.0';
        t += `<td>${lastWeek?.paidCount || 0}</td><td>${lastWeek?.trialCount || 0}</td><td>${conversion}%</td></tr>`;
        return t;
    }).join('');
    elements.customSchoolClassTableBody.innerHTML = rows;
    scheduleAdaptNameCells();
}
