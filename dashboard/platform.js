const state = {
    token: localStorage.getItem('sales-platform-token') || '',
    user: null,
    schools: [],
    imports: [],
    keySchoolImports: [],
    selectedKey: '',
    status: '',
    drillView: 'activity',
    dashboardRecords: [],
    dashboardImports: [],
    dashboardSyncText: '尚未同步数据看板原始数据',
    filters: { owner: '', province: '', city: '', district: '', students: '', trial: '' },
    currentSchool: null,
    role: 'sales',
    subAccounts: []
};

const $ = (id) => document.getElementById(id);
const LOCAL_MODE = location.protocol === 'file:' || location.hostname.endsWith('github.io');
const LOCAL_DB_KEY = 'sales-platform-local-db-v2';
const FAVORITE_KEY = 'sales-platform-favorite-schools-v1';
const ADMIN_USER = { username: 'admin', password: 'ets@admin', role: 'manager', name: '管理者', provinces: [] };
const PROVINCES = ['北京', '天津', '河北', '山西', '内蒙古', '辽宁', '吉林', '黑龙江', '上海', '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南', '湖北', '湖南', '广东', '广西', '海南', '重庆', '四川', '贵州', '云南', '西藏', '陕西', '甘肃', '青海', '宁夏', '新疆'];

function defaultLocalDb() {
    return { keySchools: [], keySchoolImports: [], records: [], imports: [], progress: {}, subAccounts: [] };
}

function loadLocalDb() {
    try { return { ...defaultLocalDb(), ...JSON.parse(localStorage.getItem(LOCAL_DB_KEY) || '{}') }; } catch { return defaultLocalDb(); }
}

function saveLocalDb(db) {
    localStorage.setItem(LOCAL_DB_KEY, JSON.stringify(db));
}

function loadFavorites() {
    try { return new Set(JSON.parse(localStorage.getItem(FAVORITE_KEY) || '[]')); } catch { return new Set(); }
}

function saveFavorites(set) {
    localStorage.setItem(FAVORITE_KEY, JSON.stringify([...set]));
}

function currentRole() {
    return state.user?.role || state.role || 'sales';
}

function isManager() {
    return currentRole() === 'manager';
}

function normalizeProvince(value = '') {
    return String(value || '')
        .replace(/壮族自治区|回族自治区|维吾尔自治区|自治区|特别行政区|省|市/g, '')
        .trim();
}

function canSeeSchool(school) {
    if (isManager()) return true;
    const provinces = (state.user?.provinces || []).map(normalizeProvince);
    return !provinces.length || provinces.includes(normalizeProvince(school.province));
}

function isFavorite(key) {
    return loadFavorites().has(key);
}

function toggleFavorite(key) {
    const set = loadFavorites();
    if (set.has(key)) set.delete(key); else set.add(key);
    saveFavorites(set);
    renderSchools();
}

function openDashboardDb() {
    return new Promise((resolve, reject) => {
        const req = indexedDB.open('EducationDataDB');
        req.onerror = () => reject(req.error || new Error('无法打开数据看板数据库'));
        req.onsuccess = () => resolve(req.result);
    });
}

function readAllDashboardFiles(db) {
    return new Promise((resolve, reject) => {
        if (!db.objectStoreNames.contains('files')) {
            reject(new Error('当前在线页面还没有可同步的数据看板文件。请先在 http://127.0.0.1:8090/index.html 上传周数据，再回到本页点击同步。浏览器的 file:// 数据不能被 http://127.0.0.1:8090 直接读取。'));
            return;
        }
        const tx = db.transaction(['files'], 'readonly');
        const req = tx.objectStore('files').getAll();
        req.onerror = () => reject(req.error || new Error('读取数据看板文件失败'));
        req.onsuccess = () => resolve(req.result || []);
    });
}

async function loadDashboardDataset() {
    if (!window.XLSX) throw new Error('Excel 解析库未加载，请确认网络可访问 CDN');
    const db = await openDashboardDb();
    const files = await readAllDashboardFiles(db);
    if (!files.length) throw new Error('当前浏览器来源下没有数据看板文件。请在同一在线地址打开 index.html 并导入周数据后再同步；如果数据在 file:// 页面中，只能被 file:// 页面读取。');
    const records = [];
    for (const file of files) {
        if (!file.data) continue;
        const buffer = await file.data.arrayBuffer();
        const wb = XLSX.read(new Uint8Array(buffer), { type: 'array' });
        const rows = XLSX.utils.sheet_to_json(wb.Sheets[wb.SheetNames[0]]);
        const info = file.dateInfo || {};
        rows.forEach(row => records.push({
            ...row,
            weekStartDate: info.startDate || row.weekStartDate || '',
            weekEndDate: info.endDate || row.weekEndDate || '',
            weekDisplay: info.fullDisplayRange || info.displayRange || row.weekDisplay || file.filename,
            importFilename: file.filename || ''
        }));
    }
    state.dashboardRecords = records;
    state.dashboardImports = files.map(file => ({
        filename: file.filename || '数据看板文件',
        rows: records.filter(row => row.importFilename === file.filename).length,
        uploadedAt: file.uploadDate || '',
        by: 'EducationDataDB'
    }));
    state.dashboardSyncText = `已引用数据看板原始数据：${files.length} 个周文件，${records.length.toLocaleString()} 行`;
}

async function syncDashboardData() {
    if (!isManager()) throw new Error('仅管理者可同步数据看板原始数据');
    await loadDashboardDataset();
    if (!LOCAL_MODE) {
        await api('/api/dashboard-sync', {
            method: 'POST',
            body: JSON.stringify({ records: state.dashboardRecords, imports: state.dashboardImports })
        });
    }
    await refresh();
    toast(state.dashboardSyncText);
}

function toast(message) {
    const el = $('toast');
    el.textContent = message;
    el.hidden = false;
    setTimeout(() => { el.hidden = true; }, 3200);
}

async function api(path, options = {}) {
    if (LOCAL_MODE) return localApi(path, options);
    const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
    if (state.token) headers.Authorization = `Bearer ${state.token}`;
    const res = await fetch(path, { ...options, headers });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || '请求失败');
    return data;
}

function pick(row, names) {
    const normalized = new Map(Object.keys(row || {}).map(key => [String(key).replace(/\s+/g, '').toLowerCase(), key]));
    for (const name of names) {
        const key = normalized.get(String(name).replace(/\s+/g, '').toLowerCase()) || name;
        if (row[key] !== undefined && row[key] !== null && String(row[key]).trim() !== '') return String(row[key]).trim();
    }
    return '';
}

function num(value) {
    const n = Number(value);
    return Number.isFinite(n) ? n : 0;
}

function localSchoolName(row) {
    return pick(row, ['学校名称', '学校', '校名', '学校全称', '学校名', '学校名字', 'schoolName', 'school']);
}

function rowClassId(row) {
    return row['班级 id'] || row['班级ID'] || row['班级id'] || row['班级 ID'] || row['classId'] || row['class_id'] || row['班级名称'] || '';
}

function localSchoolId(row) {
    return pick(row, ['学校ID', '学校 Id', '学校 id', '学校编号', '学校编码', 'schoolId', 'school_id']);
}

function localOwner(row) {
    return pick(row, ['责任人', '负责人', '对应人', '负责销售', '责任销售', '销售', '跟进人', '销售负责人', '销售责任人', 'owner', 'sales']);
}

function localCity(row) {
    return pick(row, ['地市', '城市', '市', '地级市', '所属城市', '所属地市', '地市名称', '城市名称', 'city']);
}

function localSchoolKey(row) {
    return localSchoolId(row) || localSchoolName(row);
}

function parseWeekFromName(filename = '') {
    const m = filename.match(/^(\d{4})(\d{2})(\d{2})-(\d{4})(\d{2})(\d{2})_/);
    if (!m) return {};
    const [, y1, m1, d1, y2, m2, d2] = m;
    return { weekStartDate: `${y1}-${m1}-${d1}`, weekEndDate: `${y2}-${m2}-${d2}`, weekDisplay: `${y1}-${m1}-${d1} 至 ${y2}-${m2}-${d2}` };
}

function aggregateLocalSchools(db) {
    const map = new Map();
    (db.keySchools || []).forEach(s => map.set(s.key, { ...s, classes: new Set(), grades: new Map(), weeks: new Map() }));
    const nameToKey = new Map((db.keySchools || []).filter(s => s.school).map(s => [s.school, s.key]));
    const globalLatestWeek = [...new Set((db.records || []).map(row => row.weekStartDate || '').filter(Boolean))].sort().pop() || '';

    (db.records || []).forEach(row => {
        const identity = localSchoolKey(row);
        const key = map.has(identity) ? identity : nameToKey.get(localSchoolName(row));
        if (!key || !map.has(key)) return;
        const school = map.get(key);
        school.classes.add(rowClassId(row) || `${localSchoolName(row)}-${row['年级'] || ''}`);
        const grade = row['年级'] || '未填写年级';
        if (!school.grades.has(grade)) school.grades.set(grade, []);
        school.grades.get(grade).push(row);
        const weekKey = row.weekStartDate || row.weekDisplay || '未识别周次';
        if (!school.weeks.has(weekKey)) school.weeks.set(weekKey, { startDate: row.weekStartDate || '', display: row.weekDisplay || weekKey, assignments: 0, completionSum: 0, completionCount: 0, paid: 0, trial: 0, students: 0, classes: new Set() });
        const week = school.weeks.get(weekKey);
        week.assignments += num(row['布置作业次数']);
        week.completionSum += num(row['作业完成率']) * 100;
        week.completionCount += 1;
        week.paid += num(row['未过期付费学生数']);
        week.trial += num(row['未过期试用学生数']);
        week.students += num(row['总学生数']);
        week.classes.add(rowClassId(row) || `${localSchoolName(row)}-${row['年级'] || ''}`);
    });

    return [...map.values()].map(s => {
        const weeks = [...s.weeks.values()].sort((a, b) => String(a.startDate).localeCompare(String(b.startDate)));
        const latest = weeks[weeks.length - 1] || { completion: 0, paid: 0, trial: 0, students: 0 };
        latest.completion = latest.completionCount ? latest.completionSum / latest.completionCount : 0;
        latest.avgAssignments = latest.classes?.size ? latest.assignments / latest.classes.size : 0;
        latest.payRate = latest.students > 0 ? latest.paid / latest.students * 100 : 0;
        const gradeRows = [...s.grades.entries()].map(([grade, rows]) => {
            const latestRows = globalLatestWeek ? rows.filter(r => r.weekStartDate === globalLatestWeek) : rows;
            const classCount = new Set(rows.map(r => rowClassId(r) || `${grade}-${localSchoolName(r)}`)).size;
            const students = latestRows.reduce((sum, r) => sum + num(r['总学生数']), 0);
            const paid = latestRows.reduce((sum, r) => sum + num(r['未过期付费学生数']), 0);
            const trial = latestRows.reduce((sum, r) => sum + num(r['未过期试用学生数']), 0);
            const assignments = latestRows.reduce((sum, r) => sum + num(r['布置作业次数']), 0);
            const completion = latestRows.length ? latestRows.reduce((sum, r) => sum + num(r['作业完成率']) * 100, 0) / latestRows.length : 0;
            const activeClassCount = new Set(latestRows.map(r => rowClassId(r) || `${grade}-${localSchoolName(r)}`)).size;
            return { grade, classCount, students, paid, trial, paidRate: students ? paid / students * 100 : 0, assignments, avgAssignments: activeClassCount ? assignments / activeClassCount : 0, completion };
        });
        const classRows = [];
        s.grades.forEach((rows, grade) => rows.forEach(r => classRows.push({
            grade,
            teacher: r['教师姓名'] || r['老师姓名'] || r['教师'] || '',
            className: r['班级名称'] || '',
            classId: rowClassId(r),
            students: num(r['总学生数']),
            paid: num(r['未过期付费学生数']),
            trial: num(r['未过期试用学生数']),
            assignments: num(r['布置作业次数']),
            completion: num(r['作业完成率']) * 100,
            weekDisplay: r.weekDisplay || r.weekStartDate || ''
        })));
        const hasLatestWeek = !!(globalLatestWeek && s.weeks.has(globalLatestWeek));
        const latestWeek = hasLatestWeek ? s.weeks.get(globalLatestWeek) : { completion: 0, paid: 0, trial: 0, students: 0, assignments: 0, classes: new Set() };
        latestWeek.completion = latestWeek.completionCount ? latestWeek.completionSum / latestWeek.completionCount : 0;
        latestWeek.avgAssignments = latestWeek.classes?.size ? latestWeek.assignments / latestWeek.classes.size : 0;
        latestWeek.payRate = latestWeek.students > 0 ? latestWeek.paid / latestWeek.students * 100 : 0;
        const activeGradeRows = gradeRows.filter(row => row.students > 0);
        const payRate = latestWeek.students > 0 ? latestWeek.paid / latestWeek.students * 100 : 0;
        const status = payRate > 20 ? '付费校' : (payRate < 20 && latestWeek.students > 100) ? '试用校' : '未试用校';
        const chargeGrades = activeGradeRows.filter(g => g.paidRate > 50).map(g => shortGrade(g.grade));
        return { key: s.key, schoolId: s.schoolId || '', province: s.province || '', city: s.city || '', district: s.district || '', school: s.school || '', owner: s.owner || '', classCount: s.classes.size, status, latest: latestWeek, weeks, gradeRows, classRows, chargeGrades, progress: db.progress[s.key] || { logs: [] }, globalLatestWeek };
    });
}

async function localApi(path, options = {}) {
    const db = loadLocalDb();
    const body = options.body ? JSON.parse(options.body) : {};
    const tokenUser = localStorage.getItem('sales-platform-token');
    const localUsers = [ADMIN_USER, ...(db.subAccounts || [])];
    const authUser = localUsers.find(u => u.username === tokenUser);
    if (path === '/api/login') {
        const user = localUsers.find(u => u.username === body.username && u.password === body.password);
        if (!user) throw new Error('登录失败：账号或密码错误');
        return { token: user.username, user: { username: user.username, role: user.role, name: user.name || user.username, provinces: user.provinces || [] } };
    }
    if (path === '/api/me') {
        if (!authUser) throw new Error('请先登录');
        return { user: { username: authUser.username, role: authUser.role, name: authUser.name || authUser.username, provinces: authUser.provinces || [] } };
    }
    if (!authUser && path !== '/api/login') throw new Error('请先登录');
    if (path === '/api/schools') {
        const liveDb = { ...db, records: state.dashboardRecords, imports: state.dashboardImports };
        const userProvinces = (authUser.provinces || []).map(normalizeProvince);
        const schools = aggregateLocalSchools(liveDb).filter(s => authUser.role === 'manager' || !userProvinces.length || userProvinces.includes(normalizeProvince(s.province)));
        return { schools, imports: state.dashboardImports || [], keySchoolImports: db.keySchoolImports || [], subAccounts: db.subAccounts || [] };
    }
    if (path === '/api/key-schools') {
        if (authUser.role !== 'manager') throw new Error('仅管理者可操作');
        const seen = new Set();
        db.keySchools = (body.records || []).map((row, index) => {
            const schoolId = localSchoolId(row);
            const school = localSchoolName(row);
            const key = schoolId || school;
            if (!key || seen.has(key)) return null;
            seen.add(key);
            return { key, schoolId, school, province: pick(row, ['省份', '省', 'province']), city: localCity(row), district: pick(row, ['区县', '区', '县', 'district']), owner: localOwner(row), rowIndex: index + 1 };
        }).filter(Boolean);
        db.keySchoolImports = [{ filename: body.filename || '重点校清单.xlsx', rows: db.keySchools.length, uploadedAt: new Date().toISOString(), by: 'local' }];
        saveLocalDb(db);
        return { ok: true, rows: db.keySchools.length };
    }
    if (path === '/api/import') {
        if (authUser.role !== 'manager') throw new Error('仅管理者可操作');
        const meta = parseWeekFromName(body.filename || '');
        const records = (body.records || []).map(row => ({ ...row, ...meta, importFilename: body.filename || '' }));
        db.records = (db.records || []).filter(row => row.importFilename !== body.filename);
        db.records.push(...records);
        db.imports = (db.imports || []).filter(item => item.filename !== body.filename);
        db.imports.push({ filename: body.filename || '周数据.xlsx', rows: records.length, uploadedAt: new Date().toISOString(), by: 'local' });
        saveLocalDb(db);
        return { ok: true, rows: records.length };
    }
    if (path === '/api/dashboard-sync' && options.method === 'POST') {
        if (authUser.role !== 'manager') throw new Error('仅管理者可操作');
        db.records = Array.isArray(body.records) ? body.records : [];
        db.imports = Array.isArray(body.imports) ? body.imports : [];
        saveLocalDb(db);
        return { ok: true, rows: db.records.length };
    }
    if (path === '/api/subaccounts' && (!options.method || options.method === 'GET')) {
        if (authUser.role !== 'manager') throw new Error('仅管理者可操作');
        return { subAccounts: db.subAccounts || [] };
    }
    if (path === '/api/subaccounts' && options.method === 'POST') {
        if (authUser.role !== 'manager') throw new Error('仅管理者可操作');
        const username = String(body.username || '').trim();
        if (!username || !body.password) throw new Error('请填写账号和密码');
        if (username === ADMIN_USER.username) throw new Error('不能覆盖管理者总账号');
        const provinces = Array.isArray(body.provinces) ? body.provinces : (body.province ? [body.province] : []);
        const next = { username, password: String(body.password), role: body.role === 'manager' ? 'manager' : 'sales', name: username, provinces };
        db.subAccounts = (db.subAccounts || []).filter(u => u.username !== username);
        db.subAccounts.push(next);
        saveLocalDb(db);
        return { ok: true, subAccounts: db.subAccounts };
    }
    if (path.startsWith('/api/subaccounts/') && options.method === 'DELETE') {
        if (authUser.role !== 'manager') throw new Error('仅管理者可操作');
        const username = decodeURIComponent(path.split('/').pop());
        db.subAccounts = (db.subAccounts || []).filter(u => u.username !== username);
        saveLocalDb(db);
        return { ok: true, subAccounts: db.subAccounts };
    }
    return { ok: true };
}

function formatPct(value) {
    return `${Number(value || 0).toFixed(1)}%`;
}

function shortGrade(grade = '') {
    const text = String(grade || '').replace(/年级/g, '').replace(/初/g, '').replace(/高/g, '');
    const map = { 一: '一', 二: '二', 三: '三', 四: '四', 五: '五', 六: '六', 七: '七', 八: '八', 九: '九', 1: '一', 2: '二', 3: '三', 4: '四', 5: '五', 6: '六', 7: '七', 8: '八', 9: '九' };
    const found = text.match(/[一二三四五六七八九1-9]/);
    return found ? map[found[0]] || found[0] : text.slice(0, 2);
}

function fmtTime(value) {
    if (!value) return '';
    return new Date(value).toLocaleString('zh-CN', { hour12: false });
}

function badgeClass(status) {
    if (status === '付费校') return 'status-paid';
    if (status === '试用校') return 'status-trial';
    return 'status-unused';
}

function escapeHtml(value = '') {
    return String(value ?? '').replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
}

function maxGradePaidRate(school) {
    return Math.max(0, ...(school.gradeRows || []).map(row => Number(row.paidRate || 0)));
}

function schoolPayRate(school) {
    const latest = school.latest || {};
    return latest.students > 0 ? (latest.paid || 0) / latest.students * 100 : 0;
}

function passStudentFilter(total, filter) {
    if (!filter) return true;
    if (filter === 'lt300') return total < 300;
    if (filter === '300_800') return total >= 300 && total < 800;
    if (filter === '800_1500') return total >= 800 && total < 1500;
    if (filter === 'gte1500') return total >= 1500;
    return true;
}

function passTrialFilter(total, filter) {
    if (!filter) return true;
    if (filter === 'lt300') return total < 300;
    if (filter === '300_500') return total >= 300 && total < 500;
    if (filter === '500_800') return total >= 500 && total < 800;
    if (filter === 'gte800') return total >= 800;
    return true;
}

function updateSelectOptions(selectId, values, defaultText) {
    const select = $(selectId);
    const current = select.value;
    const options = [...new Set(values.filter(Boolean))].sort((a, b) => String(a).localeCompare(String(b), 'zh-CN'));
    select.innerHTML = `<option value="">${defaultText}</option>` + options.map(v => `<option value="${escapeHtml(v)}">${escapeHtml(v)}</option>`).join('');
    if (options.includes(current)) select.value = current;
}

function renderFilterOptions() {
    updateSelectOptions('ownerFilter', state.schools.map(s => s.owner), '全部负责人');
    updateSelectOptions('provinceFilter', state.schools.map(s => s.province), '全部省份');
    updateSelectOptions('cityFilter', state.schools.filter(s => !state.filters.province || s.province === state.filters.province).map(s => s.city), '全部城市');
    updateSelectOptions('districtFilter', state.schools.filter(s => {
        if (state.filters.province && s.province !== state.filters.province) return false;
        if (state.filters.city && s.city !== state.filters.city) return false;
        return true;
    }).map(s => s.district), '全部区县');
    $('studentFilter').value = state.filters.students;
    $('trialFilter').value = state.filters.trial || '';
}

function renderDrillView() {
    const view = state.drillView || 'week';
    $('weekTable').hidden = view !== 'week';
    $('gradeTable').hidden = view !== 'grade';
    $('classTable').hidden = view !== 'class';
    $('activityView').hidden = view !== 'activity';
    $('drillTitle').textContent = view === 'grade' ? '按年级展示' : view === 'class' ? '按班级展示' : view === 'activity' ? '学校动态' : '周历史数据';
    document.querySelectorAll('#drillTabs .tab').forEach(btn => btn.classList.toggle('active', btn.dataset.view === view));
}

function todayKey() {
    const d = new Date();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${d.getFullYear()}-${m}-${day}`;
}

function progressStore() {
    const db = loadLocalDb();
    db.progress = db.progress || {};
    return db;
}

function getSchoolProgress(key) {
    if (!LOCAL_MODE) return state.schools.find(s => s.key === key)?.progress || { daily: {}, managerReplies: [] };
    const db = loadLocalDb();
    return db.progress?.[key] || { daily: {}, managerReplies: [] };
}

function saveSchoolProgress(key, progress) {
    const db = progressStore();
    db.progress[key] = progress;
    saveLocalDb(db);
}

function renderActivity(school) {
    const progress = getSchoolProgress(school.key);
    const day = todayKey();
    $('dailyProgressInput').value = progress.daily?.[day]?.text || '';
    $('managerReplyInput').value = '';
    const dailyItems = Object.entries(progress.daily || {}).map(([date, item]) => ({ type: '销售进展', date, text: item.text || '', editable: date === day }));
    const items = dailyItems.sort((a, b) => String(b.date).localeCompare(String(a.date)));
    $('activityEditorTitle').textContent = isManager() ? '进展回复' : '今日销售进展';
    $('dailyProgressInput').closest('label').hidden = isManager();
    $('saveDailyProgressBtn').hidden = isManager();
    $('managerReplyInput').closest('label').hidden = !isManager();
    $('saveManagerReplyBtn').hidden = !isManager();
    $('activityHistoryTitle').textContent = isManager() ? '学校进展查看' : '历史进展';
    $('activityTimeline').innerHTML = items.length ? items.map(item => `<div class="timeline-item">
        <strong>${escapeHtml(item.type)} · ${escapeHtml(item.date)}${item.editable ? ' · 可编辑' : ''}</strong>
        <div>${escapeHtml(item.text)}</div>
    </div>`).join('') : '<div class="timeline-empty">暂无进展动态</div>';
    const replies = progress.managerReplies || [];
    $('managerProgressView').innerHTML = `<h4>管理回复</h4>${replies.length ? replies.map((reply, index) => {
        const replyId = reply.id || String(index);
        return `<div class="reply-item">
            <strong>${escapeHtml(reply.date || '')}${reply.progressDate ? ` · 对 ${escapeHtml(reply.progressDate)} 进展` : ''}</strong>
            ${isManager()
                ? `<textarea data-manager-reply-input="${escapeHtml(replyId)}">${escapeHtml(reply.text || '')}</textarea>
                   <button class="secondary-btn" data-update-manager-reply="${escapeHtml(replyId)}">保存修改</button>`
                : `<div>${escapeHtml(reply.text || '')}</div>`}
        </div>`;
    }).join('') : '<div class="timeline-empty">暂无管理回复</div>'}`;
    $('salesReplyView').innerHTML = '';
}

function allProgressItems() {
    const progress = LOCAL_MODE
        ? loadLocalDb().progress || {}
        : Object.fromEntries(state.schools.map(s => [s.key, s.progress || { daily: {}, managerReplies: [] }]));
    const schoolMap = new Map(state.schools.map(s => [s.key, s]));
    const progressItems = [];
    const replyItems = [];
    Object.entries(progress).forEach(([schoolKey, item]) => {
        const school = schoolMap.get(schoolKey);
        const schoolName = school?.school || schoolKey;
        Object.entries(item.daily || {}).forEach(([date, daily]) => {
            if (daily?.text) progressItems.push({ date, schoolKey, schoolName, owner: school?.owner || '', text: daily.text });
        });
        (item.managerReplies || []).forEach((reply, index) => {
            if (reply?.text) replyItems.push({ id: reply.id || String(index), date: reply.date || '', schoolKey, schoolName, owner: school?.owner || '', text: reply.text, progressDate: reply.progressDate || '' });
        });
    });
    const newestFirst = (a, b) => String(b.date).localeCompare(String(a.date));
    return {
        progressItems: progressItems.sort(newestFirst),
        replyItems: replyItems.sort(newestFirst)
    };
}

function salesScopeKeys() {
    if (isManager()) return new Set(state.schools.map(s => s.key));
    return new Set(state.schools.filter(canSeeSchool).map(s => s.key));
}

function renderGlobalTimelines() {
    $('globalActivityPanel').hidden = false;
    const { progressItems, replyItems } = allProgressItems();
    const visibleKeys = salesScopeKeys();
    const visibleProgressItems = !isManager() ? progressItems.filter(item => visibleKeys.has(item.schoolKey)) : progressItems;
    const visibleReplyItems = !isManager() ? replyItems.filter(item => visibleKeys.has(item.schoolKey)) : replyItems;
    $('globalReplyPanel').hidden = false;
    $('globalProgressTimeline').innerHTML = visibleProgressItems.length ? visibleProgressItems.map((item, index) => {
        const textareaId = `managerGlobalReply-${index}`;
        return `<div class="timeline-item progress-thread">
        <strong>${escapeHtml(item.date)} · ${escapeHtml(item.schoolName)}${item.owner ? ` · ${escapeHtml(item.owner)}` : ''}</strong>
        <div>${escapeHtml(item.text)}</div>
        ${isManager() ? `<div class="inline-reply-editor">
            <textarea id="${textareaId}" placeholder="针对该进展直接回复"></textarea>
            <button class="secondary-btn" data-save-global-reply="${escapeHtml(item.schoolKey)}" data-progress-date="${escapeHtml(item.date)}" data-reply-input="${textareaId}">回复</button>
        </div>` : ''}
    </div>`;
    }).join('') : '<div class="timeline-empty">暂无销售进展</div>';
    $('globalReplyTimeline').innerHTML = visibleReplyItems.length ? visibleReplyItems.map(item => `<div class="timeline-item">
        <strong>${escapeHtml(item.date)} · ${escapeHtml(item.schoolName)}${item.progressDate ? ` · 对 ${escapeHtml(item.progressDate)} 进展` : ''}</strong>
        <div>${escapeHtml(item.text)}</div>
    </div>`).join('') : '<div class="timeline-empty">暂无管理回复</div>';
}

function renderClassComparisonTable(school) {
    const rows = school.classRows || [];
    const table = $('classTable');
    if (!rows.length) {
        table.querySelector('thead').innerHTML = '<tr><th>班级明细</th></tr>';
        $('classRows').innerHTML = '<tr><td style="text-align:center;color:#94a3b8;padding:24px;">暂无班级数据</td></tr>';
        return;
    }
    const weekKeys = [...new Set(rows.map(r => r.weekDisplay || '未识别周次'))].sort();
    const groupMap = new Map();
    rows.forEach(row => {
        const key = `${row.grade || ''}|${row.teacher || ''}|${row.className || row.classId || ''}`;
        if (!groupMap.has(key)) groupMap.set(key, {
            grade: row.grade || '-',
            teacher: row.teacher || '-',
            className: row.className || row.classId || '-',
            weeks: new Map(),
            latest: row
        });
        const group = groupMap.get(key);
        group.weeks.set(row.weekDisplay || '未识别周次', row);
        if (String(row.weekDisplay || '').localeCompare(String(group.latest.weekDisplay || ''), 'zh-CN') >= 0) group.latest = row;
    });

    const visibleWeeks = weekKeys.slice(-4);
    table.querySelector('thead').innerHTML = `<tr>
        <th>年级</th>
        <th>老师</th>
        <th>班级</th>
        ${visibleWeeks.map(week => `<th>${escapeHtml(week)}<br>布置/完成</th>`).join('')}
        <th>学生</th>
        <th>付费</th>
        <th>试用</th>
        <th>付费率</th>
    </tr>`;
    $('classRows').innerHTML = [...groupMap.values()].map(group => {
        const latest = group.latest || {};
        const payRate = latest.students > 0 ? latest.paid / latest.students * 100 : 0;
        return `<tr>
            <td>${escapeHtml(group.grade)}</td>
            <td>${escapeHtml(group.teacher)}</td>
            <td class="class-name-cell">${escapeHtml(group.className)}</td>
            ${visibleWeeks.map(week => {
                const row = group.weeks.get(week);
                return row ? `<td>${Number(row.assignments || 0).toLocaleString()} / ${formatPct(row.completion)}</td>` : '<td>-</td>';
            }).join('')}
            <td>${Number(latest.students || 0).toLocaleString()}</td>
            <td>${Number(latest.paid || 0).toLocaleString()}</td>
            <td>${Number(latest.trial || 0).toLocaleString()}</td>
            <td>${formatPct(payRate)}</td>
        </tr>`;
    }).join('');
}

async function login() {
    const username = $('usernameInput').value.trim();
    const password = $('passwordInput').value;
    const data = await api('/api/login', {
        method: 'POST',
        body: JSON.stringify({ username, password })
    });
    state.token = data.token;
    state.user = data.user;
    state.role = data.user.role;
    localStorage.setItem('sales-platform-token', state.token);
    await refresh();
}

function logout() {
    state.token = '';
    state.user = null;
    localStorage.removeItem('sales-platform-token');
    $('loginView').hidden = false;
    $('platformView').hidden = true;
}

async function loadMe() {
    if (!state.token) return false;
    try {
        const data = await api('/api/me');
        state.user = data.user;
        state.role = data.user.role;
        return true;
    } catch {
        logout();
        return false;
    }
}

function showLogin() {
    $('loginView').hidden = false;
    $('platformView').hidden = true;
}

async function refresh() {
    if (LOCAL_MODE) {
        try {
            await loadDashboardDataset();
        } catch (err) {
            state.dashboardRecords = [];
            state.dashboardImports = [];
            state.dashboardSyncText = `未读取到数据看板原始数据：${err.message}`;
        }
    }
    const data = await api('/api/schools');
    state.schools = data.schools || [];
    state.imports = data.imports || [];
    state.keySchoolImports = data.keySchoolImports || [];
    state.subAccounts = data.subAccounts || [];
    if (!LOCAL_MODE) {
        const rows = state.imports.reduce((sum, item) => sum + Number(item.rows || 0), 0);
        state.dashboardSyncText = state.imports.length
            ? `已同步数据看板原始数据：${state.imports.length} 个周文件，${rows.toLocaleString()} 行`
            : '尚未同步数据看板原始数据';
    }
    render();
}

function render() {
    $('loginView').hidden = true;
    $('platformView').hidden = false;
    state.role = state.user?.role || state.role;
    const provinceText = state.user?.provinces?.length ? ` · ${state.user.provinces.join('、')}` : '';
    $('userMeta').textContent = `${isManager() ? '管理者' : '销售'}：${state.user?.username || '-'}${provinceText}`;
    $('managerUploadPanel').hidden = !isManager();
    $('accountManageBtn').hidden = !isManager();
    document.querySelectorAll('.manager-only').forEach(el => { el.hidden = !isManager(); });

    renderSummary();
    renderImports();
    renderSchools();
    renderGlobalTimelines();
    renderSubAccounts();
}

function renderSummary() {
    const counts = state.schools.reduce((acc, s) => {
        acc[s.status] = (acc[s.status] || 0) + 1;
        return acc;
    }, { '未试用校': 0, '试用校': 0, '付费校': 0 });
    $('unusedCount').textContent = counts['未试用校'];
    $('trialCount').textContent = counts['试用校'];
    $('paidCount').textContent = counts['付费校'];
    $('visibleCount').textContent = state.schools.length;
}

function currentListType() {
    return state.status || '全部';
}

function filteredSchools() {
    const keyword = $('searchInput').value.trim().toLowerCase();
    return state.schools.filter(s => {
        if (!canSeeSchool(s)) return false;
        if (state.status === '收藏校' && !isFavorite(s.key)) return false;
        if (state.status && state.status !== '收藏校' && s.status !== state.status) return false;
        if (state.filters.owner && s.owner !== state.filters.owner) return false;
        if (state.filters.province && s.province !== state.filters.province) return false;
        if (state.filters.city && s.city !== state.filters.city) return false;
        if (state.filters.district && s.district !== state.filters.district) return false;
        if (!passStudentFilter(Number(s.latest?.students || 0), state.filters.students)) return false;
        if (!passTrialFilter(Number(s.latest?.trial || 0), state.filters.trial)) return false;
        if (!keyword) return true;
        return String(s.school || '').toLowerCase().includes(keyword);
    }).sort((a, b) => {
        const order = { '付费校': 0, '试用校': 1, '未试用校': 2 };
        return (order[a.status] - order[b.status]) || a.school.localeCompare(b.school, 'zh-CN');
    });
}

function renderSchoolTableHead(type) {
    const commonStart = ['负责人', '城市', '区县', '学校', '学校定义'];
    let cols;
    if (type === '付费校') {
        cols = [...commonStart, '收费年级', '学生总数', '未过期付费人数', '未过期试用人数', '付费率', '操作', '收藏'];
    } else if (type === '未试用校') {
        cols = [...commonStart, '学生总数', '操作', '收藏'];
    } else {
        cols = [...commonStart, '涉及年级数', '班级总数', '学生总数', '未过期付费人数', '未过期试用人数', '付费率', '操作', '收藏'];
    }
    $('schoolTableHead').innerHTML = `<tr>${cols.map(c => `<th>${c}</th>`).join('')}</tr>`;
}

function actionLabel() {
    return isManager() ? '回复' : '进展跟进';
}

function renderSchoolRow(s, type) {
    const start = `
        <td>${escapeHtml(s.owner || '-')}</td>
        <td>${escapeHtml(s.city || '-')}</td>
        <td>${escapeHtml(s.district || '-')}</td>
        <td class="school-name-cell"><button class="school-button" data-school-key="${escapeHtml(s.key)}">${escapeHtml(s.school)}</button></td>
        <td><span class="badge ${badgeClass(s.status)}">${escapeHtml(s.status)}</span></td>`;
    const action = `<td><button class="mini-action-btn" data-school-key="${escapeHtml(s.key)}" data-open-activity="1">${actionLabel()}</button><button class="mini-action-btn" data-school-key="${escapeHtml(s.key)}" data-open-grade="1">年级</button></td>`;
    const fav = `<td><button class="favorite-btn" data-favorite-key="${escapeHtml(s.key)}">${isFavorite(s.key) ? '★' : '☆'}</button></td>`;
    if (type === '付费校') {
        return `<tr class="${state.selectedKey === s.key ? 'selected' : ''}">${start}<td>${escapeHtml((s.chargeGrades || []).join('、') || '-')}</td><td>${Number(s.latest?.students || 0).toLocaleString()}</td><td>${Number(s.latest?.paid || 0).toLocaleString()}</td><td>${Number(s.latest?.trial || 0).toLocaleString()}</td><td>${formatPct(schoolPayRate(s))}</td>${action}${fav}</tr>`;
    }
    if (type === '未试用校') {
        return `<tr class="${state.selectedKey === s.key ? 'selected' : ''}">${start}<td>${Number(s.latest?.students || 0).toLocaleString()}</td>${action}${fav}</tr>`;
    }
    return `<tr class="${state.selectedKey === s.key ? 'selected' : ''}">${start}<td>${(s.gradeRows || []).length}</td><td>${s.classCount || 0}</td><td>${Number(s.latest?.students || 0).toLocaleString()}</td><td>${Number(s.latest?.paid || 0).toLocaleString()}</td><td>${Number(s.latest?.trial || 0).toLocaleString()}</td><td>${formatPct(schoolPayRate(s))}</td>${action}${fav}</tr>`;
}

function renderSchools() {
    document.querySelectorAll('#statusTabs .tab').forEach(btn => btn.classList.toggle('active', (btn.dataset.status || '') === state.status));
    renderFilterOptions();
    const type = currentListType();
    renderSchoolTableHead(type);
    const rows = filteredSchools();
    $('schoolRows').innerHTML = rows.length ? rows.map(s => {
        return renderSchoolRow(s, type);
    }).join('') : '<tr><td colspan="12" style="text-align:center;color:#94a3b8;padding:28px;">当前条件下暂无学校</td></tr>';

    const selected = rows.find(s => s.key === state.selectedKey) || rows[0];
    if (selected) {
        state.selectedKey = selected.key;
        renderDetail(selected);
    } else {
        state.selectedKey = '';
        $('emptyDetail').hidden = false;
        $('detailContent').hidden = true;
    }
    renderGlobalTimelines();
}

function renderDetail(school) {
    state.currentSchool = school;
    $('emptyDetail').hidden = true;
    $('detailContent').hidden = false;
    $('detailName').textContent = school.school;
    $('detailMeta').textContent = `${school.province || '-'} / ${school.city || '-'} / ${school.district || '-'} · 负责人：${school.owner || '-'}${school.schoolId ? ` · ID：${school.schoolId}` : ''}`;
    $('detailStatus').textContent = school.status;
    $('detailStatus').className = `badge ${badgeClass(school.status)}`;
    const latest = school.latest || {};
    $('detailMetrics').innerHTML = [
        ['涉及年级', (school.gradeRows || []).length],
        ['学生总数', Number(latest.students || 0).toLocaleString()],
        ['未过期付费人数', Number(latest.paid || 0).toLocaleString()],
        ['未过期试用人数', Number(latest.trial || 0).toLocaleString()],
        ['付费率', formatPct(schoolPayRate(school))]
    ].map(([k, v]) => `<div><span>${k}</span><strong>${v}</strong></div>`).join('');

    $('historyRows').innerHTML = (school.weeks || []).map(w => {
        const completion = w.completionCount ? w.completionSum / w.completionCount : 0;
        const classCount = w.classes?.size || w.classCount || 0;
        const avgAssignments = classCount ? w.assignments / classCount : 0;
        return `<tr>
            <td>${escapeHtml(w.display || w.startDate)}</td>
            <td>${Number(avgAssignments || 0).toFixed(1)}</td>
            <td>${formatPct(completion)}</td>
        </tr>`;
    }).join('');

    $('gradeRows').innerHTML = (school.gradeRows || []).length ? school.gradeRows.map(row => `<tr>
        <td>${escapeHtml(row.grade)}</td>
        <td>${row.classCount || 0}</td>
        <td>${Number(row.students || 0).toLocaleString()}</td>
        <td>${formatPct(row.paidRate)}</td>
        <td>${Number(row.avgAssignments || 0).toFixed(1)}</td>
        <td>${formatPct(row.completion)}</td>
    </tr>`).join('') : '<tr><td colspan="6" style="text-align:center;color:#94a3b8;padding:24px;">暂无年级数据</td></tr>';

    renderClassComparisonTable(school);
    renderActivity(school);

    renderDrillView();

}

function saveDailyProgress() {
    if (!state.currentSchool) return;
    if (!LOCAL_MODE) {
        api('/api/progress', {
            method: 'POST',
            body: JSON.stringify({ schoolKey: state.currentSchool.key, text: $('dailyProgressInput').value.trim(), date: todayKey() })
        }).then(refresh).then(() => toast('今日销售进展已保存')).catch(err => toast(err.message));
        return;
    }
    const progress = getSchoolProgress(state.currentSchool.key);
    progress.daily = progress.daily || {};
    const day = todayKey();
    progress.daily[day] = { text: $('dailyProgressInput').value.trim(), updatedAt: new Date().toISOString() };
    saveSchoolProgress(state.currentSchool.key, progress);
    renderActivity(state.currentSchool);
    renderGlobalTimelines();
    toast('今日销售进展已保存');
}

function saveManagerReplyLocal() {
    if (!state.currentSchool) return;
    const text = $('managerReplyInput').value.trim();
    if (!text) return toast('请先填写管理回复');
    if (!LOCAL_MODE) {
        api('/api/reply', {
            method: 'POST',
            body: JSON.stringify({ schoolKey: state.currentSchool.key, reply: text, date: todayKey() })
        }).then(refresh).then(() => toast('管理回复已保存')).catch(err => toast(err.message));
        return;
    }
    const progress = getSchoolProgress(state.currentSchool.key);
    progress.managerReplies = progress.managerReplies || [];
    progress.managerReplies.push({ id: `${Date.now()}`, text, date: todayKey(), createdAt: new Date().toISOString() });
    saveSchoolProgress(state.currentSchool.key, progress);
    $('managerReplyInput').value = '';
    renderActivity(state.currentSchool);
    renderGlobalTimelines();
    toast('管理回复已保存');
}

function saveManagerReplyForSchool(schoolKey, text, progressDate = '') {
    if (!schoolKey) return;
    const reply = text.trim();
    if (!reply) return toast('请先填写管理回复');
    if (!LOCAL_MODE) {
        api('/api/reply', {
            method: 'POST',
            body: JSON.stringify({ schoolKey, reply, date: todayKey(), progressDate })
        }).then(refresh).then(() => toast('管理回复已保存')).catch(err => toast(err.message));
        return;
    }
    const progress = getSchoolProgress(schoolKey);
    progress.managerReplies = progress.managerReplies || [];
    progress.managerReplies.push({ id: `${Date.now()}`, text: reply, date: todayKey(), progressDate, createdAt: new Date().toISOString() });
    saveSchoolProgress(schoolKey, progress);
    if (state.currentSchool?.key === schoolKey) renderActivity(state.currentSchool);
    renderGlobalTimelines();
    toast('管理回复已保存');
}

function saveManagerReplyEdit(replyId, text) {
    if (!state.currentSchool) return;
    const reply = text.trim();
    if (!reply) return toast('管理回复不能为空');
    if (!LOCAL_MODE) {
        api('/api/reply', {
            method: 'POST',
            body: JSON.stringify({ schoolKey: state.currentSchool.key, reply, replyId, date: todayKey() })
        }).then(refresh).then(() => toast('管理回复已更新')).catch(err => toast(err.message));
        return;
    }
    const progress = getSchoolProgress(state.currentSchool.key);
    progress.managerReplies = progress.managerReplies || [];
    const index = progress.managerReplies.findIndex((item, i) => (item.id || String(i)) === replyId);
    if (index < 0) return toast('未找到要修改的回复');
    progress.managerReplies[index] = { ...progress.managerReplies[index], id: progress.managerReplies[index].id || replyId, text: reply, updatedAt: new Date().toISOString() };
    saveSchoolProgress(state.currentSchool.key, progress);
    renderActivity(state.currentSchool);
    renderGlobalTimelines();
    toast('管理回复已更新');
}

function setRole(role) {
    if (state.user) role = state.user.role;
    state.role = role;
    document.querySelectorAll('#roleToggle .tab').forEach(btn => btn.classList.toggle('active', btn.dataset.role === role));
    if (state.currentSchool) renderDetail(state.currentSchool);
    renderSchools();
    renderGlobalTimelines();
}

function renderImports() {
    $('keySchoolImportList').innerHTML = state.keySchoolImports.length
        ? state.keySchoolImports.slice().reverse().map(i => `<div class="import-item">
            <span>重点校清单：${escapeHtml(i.filename)}</span>
            <span>${i.rows || 0} 所 · ${fmtTime(i.uploadedAt)}</span>
        </div>`).join('')
        : '<div class="import-item"><span>尚未上传重点校清单</span></div>';
    $('dashboardDataStatus').innerHTML = `<div class="import-item"><span>${escapeHtml(state.dashboardSyncText)}</span></div>`;
    $('importList').innerHTML = state.imports.length
        ? state.imports.slice().reverse().map(i => `<div class="import-item">
            <span>引用周数据：${escapeHtml(i.filename)}</span>
            <span>${i.rows || 0} 行</span>
        </div>`).join('')
        : '<div class="import-item"><span>数据看板暂无可引用周数据</span></div>';
}

function renderProvinceOptions() {
    const selected = new Set([...$('subProvinceInput').selectedOptions].map(option => option.value));
    $('subProvinceInput').innerHTML = PROVINCES.map(p => `<option value="${p}" ${selected.has(p) ? 'selected' : ''}>${p}</option>`).join('');
}

function renderSubAccounts() {
    if (!$('subAccountList')) return;
    renderProvinceOptions();
    $('subAccountList').innerHTML = state.subAccounts.length
        ? state.subAccounts.map(account => `<div class="sub-account-item">
            <div>
                <strong>${escapeHtml(account.username)}</strong>
                <span>${account.role === 'manager' ? '管理者' : '销售'} · ${(account.provinces || []).map(escapeHtml).join('、') || '全部省份'}</span>
            </div>
            <button class="ghost-btn" data-delete-sub-account="${escapeHtml(account.username)}">删除</button>
        </div>`).join('')
        : '<div class="timeline-empty">暂无子账号</div>';
}

function selectedProvinceValues() {
    return [...$('subProvinceInput').selectedOptions].map(option => option.value);
}

async function saveSubAccount() {
    await api('/api/subaccounts', {
        method: 'POST',
        body: JSON.stringify({
            username: $('subUsernameInput').value.trim(),
            password: $('subPasswordInput').value,
            role: $('subRoleInput').value,
            provinces: selectedProvinceValues()
        })
    });
    $('subUsernameInput').value = '';
    $('subPasswordInput').value = '';
    toast('子账号已保存');
    await refresh();
}

async function deleteSubAccount(username) {
    await api(`/api/subaccounts/${encodeURIComponent(username)}`, { method: 'DELETE' });
    toast('子账号已删除');
    await refresh();
}

async function importExcel(file) {
    if (!file) return;
    if (!window.XLSX) throw new Error('Excel 解析库未加载，请确认网络可访问 CDN');
    const buf = await file.arrayBuffer();
    const wb = XLSX.read(new Uint8Array(buf), { type: 'array' });
    const records = XLSX.utils.sheet_to_json(wb.Sheets[wb.SheetNames[0]]);
    const data = await api('/api/import', {
        method: 'POST',
        body: JSON.stringify({ filename: file.name, records })
    });
    toast(`上传成功：${data.rows} 行`);
    await refresh();
}

async function importKeySchoolExcel(file) {
    if (!file) return;
    if (!window.XLSX) throw new Error('Excel 解析库未加载，请确认网络可访问 CDN');
    const buf = await file.arrayBuffer();
    const wb = XLSX.read(new Uint8Array(buf), { type: 'array' });
    const records = XLSX.utils.sheet_to_json(wb.Sheets[wb.SheetNames[0]]);
    const data = await api('/api/key-schools', {
        method: 'POST',
        body: JSON.stringify({ filename: file.name, records })
    });
    toast(`重点校清单上传成功：${data.rows} 所`);
    await refresh();
}

function bindEvents() {
    if ($('loginBtn')) $('loginBtn').onclick = () => login().catch(err => toast(err.message));
    if ($('passwordInput')) $('passwordInput').onkeydown = (e) => { if (e.key === 'Enter') login().catch(err => toast(err.message)); };
    if ($('logoutBtn')) $('logoutBtn').onclick = logout;
    $('accountManageBtn').onclick = () => { $('accountPanel').hidden = false; renderSubAccounts(); };
    $('closeAccountPanelBtn').onclick = () => { $('accountPanel').hidden = true; };
    $('saveSubAccountBtn').onclick = () => saveSubAccount().catch(err => toast(err.message));
    $('subAccountList').onclick = (e) => {
        const btn = e.target.closest('[data-delete-sub-account]');
        if (!btn) return;
        deleteSubAccount(btn.dataset.deleteSubAccount).catch(err => toast(err.message));
    };
    $('searchInput').oninput = renderSchools;
    ['ownerFilter', 'provinceFilter', 'cityFilter', 'districtFilter', 'studentFilter', 'trialFilter'].forEach(id => {
        $(id).onchange = () => {
            state.filters.owner = $('ownerFilter').value;
            state.filters.province = $('provinceFilter').value;
            state.filters.city = $('cityFilter').value;
            state.filters.district = $('districtFilter').value;
            state.filters.students = $('studentFilter').value;
            state.filters.trial = $('trialFilter').value;
            if (id === 'provinceFilter') {
                state.filters.city = '';
                state.filters.district = '';
                $('cityFilter').value = '';
                $('districtFilter').value = '';
            }
            if (id === 'cityFilter') {
                state.filters.district = '';
                $('districtFilter').value = '';
            }
            renderSchools();
        };
    });
    $('statusTabs').onclick = (e) => {
        const tab = e.target.closest('.tab');
        if (!tab) return;
        state.status = tab.dataset.status || '';
        renderSchools();
    };
    $('schoolRows').onclick = (e) => {
        const fav = e.target.closest('[data-favorite-key]');
        if (fav) {
            toggleFavorite(fav.dataset.favoriteKey);
            return;
        }
        const btn = e.target.closest('[data-school-key]');
        if (!btn) return;
        state.selectedKey = btn.dataset.schoolKey;
        if (btn.dataset.openClass) state.drillView = 'class';
        if (btn.dataset.openGrade) state.drillView = 'grade';
        if (btn.dataset.openActivity) state.drillView = 'activity';
        renderSchools();
        if (btn.dataset.openActivity) {
            const target = isManager() ? $('managerReplyInput') : $('dailyProgressInput');
            setTimeout(() => target?.focus(), 0);
        }
    };
    $('roleToggle').onclick = (e) => {
        const btn = e.target.closest('[data-role]');
        if (!btn) return;
        setRole(btn.dataset.role);
    };
    $('drillTabs').onclick = (e) => {
        const tab = e.target.closest('.tab');
        if (!tab) return;
        state.drillView = tab.dataset.view || 'week';
        renderDrillView();
    };
    $('keySchoolFileInput').onchange = (e) => {
        importKeySchoolExcel(e.target.files?.[0]).catch(err => toast(err.message));
        e.target.value = '';
    };
    $('syncDashboardDataBtn').onclick = () => syncDashboardData().catch(err => toast(err.message));
    $('refreshDataBtn').onclick = () => refresh().then(() => toast('已刷新最新数据看板数据')).catch(err => toast(err.message));
    $('saveDailyProgressBtn').onclick = saveDailyProgress;
    $('saveManagerReplyBtn').onclick = saveManagerReplyLocal;
    $('activityView').onclick = (e) => {
        const btn = e.target.closest('[data-update-manager-reply]');
        if (!btn) return;
        const replyId = btn.dataset.updateManagerReply;
        const input = document.querySelector(`[data-manager-reply-input="${CSS.escape(replyId)}"]`);
        saveManagerReplyEdit(replyId, input?.value || '');
    };
    $('globalActivityPanel').onclick = (e) => {
        const btn = e.target.closest('[data-save-global-reply]');
        if (!btn) return;
        const input = $(btn.dataset.replyInput);
        saveManagerReplyForSchool(btn.dataset.saveGlobalReply, input?.value || '', btn.dataset.progressDate || '');
    };
    setRole(state.role);
}

bindEvents();
(async function init() {
    if (!state.token) {
        showLogin();
        return;
    }
    const ok = await loadMe();
    if (!ok) return;
    await refresh();
})().catch(err => {
    showLogin();
    toast(err.message);
});
