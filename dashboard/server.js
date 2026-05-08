const crypto = require('crypto');
const fs = require('fs');
const http = require('http');
const path = require('path');
const { URL } = require('url');

const PORT = Number(process.env.PORT || 8090);
const ROOT = __dirname;
const DATA_DIR = path.join(ROOT, 'data');
const DB_PATH = path.join(DATA_DIR, 'platform-db.json');

const ADMIN_USER = { username: 'admin', password: 'ets@admin', role: 'manager', name: '管理者', provinces: [] };

const sessions = new Map();

const mimeTypes = {
    '.html': 'text/html; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.svg': 'image/svg+xml'
};

function defaultDb() {
    return {
        keySchools: [],
        keySchoolImports: [],
        records: [],
        imports: [],
        progress: {},
        subAccounts: []
    };
}

function ensureDb() {
    if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
    if (!fs.existsSync(DB_PATH)) fs.writeFileSync(DB_PATH, JSON.stringify(defaultDb(), null, 2));
}

function readDb() {
    ensureDb();
    try {
        return { ...defaultDb(), ...JSON.parse(fs.readFileSync(DB_PATH, 'utf8')) };
    } catch {
        return defaultDb();
    }
}

function writeDb(db) {
    ensureDb();
    fs.writeFileSync(DB_PATH, JSON.stringify(db, null, 2));
}

function sendJson(res, status, payload) {
    res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify(payload));
}

function setCorsHeaders(req, res) {
    const origin = req.headers.origin || '*';
    res.setHeader('Access-Control-Allow-Origin', origin);
    res.setHeader('Vary', 'Origin');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    res.setHeader('Access-Control-Allow-Methods', 'GET,POST,DELETE,OPTIONS');
}

function readBody(req) {
    return new Promise((resolve, reject) => {
        let body = '';
        req.on('data', chunk => {
            body += chunk;
            if (body.length > 20 * 1024 * 1024) {
                req.destroy();
                reject(new Error('请求体过大'));
            }
        });
        req.on('end', () => {
            if (!body) return resolve({});
            try { resolve(JSON.parse(body)); } catch { reject(new Error('JSON 格式错误')); }
        });
        req.on('error', reject);
    });
}

function tokenFromReq(req) {
    const auth = req.headers.authorization || '';
    if (auth.startsWith('Bearer ')) return auth.slice(7);
    return '';
}

function currentUser(req) {
    const token = tokenFromReq(req);
    const username = sessions.get(token);
    if (!username) return null;
    const db = readDb();
    const user = [ADMIN_USER, ...(db.subAccounts || [])].find(u => u.username === username);
    return user ? { username: user.username, role: user.role, name: user.name || user.username, provinces: user.provinces || [] } : null;
}

function requireUser(req, res) {
    const user = currentUser(req);
    if (!user) sendJson(res, 401, { error: '请先登录' });
    return user;
}

function requireManager(req, res) {
    const user = requireUser(req, res);
    if (!user) return null;
    if (user.role !== 'manager') {
        sendJson(res, 403, { error: '仅管理者可操作' });
        return null;
    }
    return user;
}

function normalizeProvince(value = '') {
    return String(value || '')
        .replace(/壮族自治区|回族自治区|维吾尔自治区|自治区|特别行政区|省|市/g, '')
        .trim();
}

function canAccessSchool(user, school) {
    if (user.role === 'manager') return true;
    const provinces = (user.provinces || []).map(normalizeProvince);
    return !provinces.length || provinces.includes(normalizeProvince(school.province));
}

function schoolKey(r) {
    return `${getProvince(r) || ''}|${getCity(r) || ''}|${getDistrict(r) || ''}|${getSchoolName(r) || ''}`;
}

function pick(r, names) {
    const normalized = new Map(Object.keys(r || {}).map(key => [String(key).replace(/\s+/g, '').toLowerCase(), key]));
    for (const name of names) {
        const key = normalized.get(String(name).replace(/\s+/g, '').toLowerCase()) || name;
        if (r[key] !== undefined && r[key] !== null && String(r[key]).trim() !== '') return String(r[key]).trim();
    }
    return '';
}

function getSchoolName(r) {
    return pick(r, ['学校名称', '学校', '校名', '学校全称', '学校名', '学校名字', 'schoolName', 'school']);
}

function getSchoolId(r) {
    return pick(r, ['学校ID', '学校 Id', '学校 id', '学校编号', '学校编码', 'schoolId', 'school_id']);
}

function getOwner(r) {
    return pick(r, ['责任人', '负责人', '对应人', '负责销售', '责任销售', '销售', '跟进人', '销售负责人', '销售责任人', 'owner', 'sales']);
}

function getProvince(r) {
    return pick(r, ['省份', '省', 'province']);
}

function getCity(r) {
    return pick(r, ['地市', '城市', '市', '地级市', '所属城市', '所属地市', '地市名称', '城市名称', 'city']);
}

function getDistrict(r) {
    return pick(r, ['区县', '区', '县', 'district']);
}

function schoolIdentity(r) {
    return getSchoolId(r) || getSchoolName(r);
}

function getClassId(r) {
    return r['班级 id'] || r['班级ID'] || r['班级id'] || r['班级 ID'] || r['classId'] || r['class_id'] || '';
}

function toNumber(value) {
    const n = Number(value);
    return Number.isFinite(n) ? n : 0;
}

function shortGrade(grade = '') {
    const text = String(grade || '').replace(/年级/g, '').replace(/初/g, '').replace(/高/g, '');
    const map = { 一: '一', 二: '二', 三: '三', 四: '四', 五: '五', 六: '六', 七: '七', 八: '八', 九: '九', 1: '一', 2: '二', 3: '三', 4: '四', 5: '五', 6: '六', 7: '七', 8: '八', 9: '九' };
    const found = text.match(/[一二三四五六七八九1-9]/);
    return found ? map[found[0]] || found[0] : text.slice(0, 2);
}

function parseFilename(filename = '') {
    const m = filename.match(/^(\d{4})(\d{2})(\d{2})-(\d{4})(\d{2})(\d{2})_/);
    if (!m) return {};
    const [, y1, m1, d1, y2, m2, d2] = m;
    return {
        weekStartDate: `${y1}-${m1}-${d1}`,
        weekEndDate: `${y2}-${m2}-${d2}`,
        weekDisplay: `${y1}-${m1}-${d1} 至 ${y2}-${m2}-${d2}`
    };
}

function aggregateSchools(records, db, user = { role: 'manager', username: 'manager' }) {
    const keySchools = db.keySchools || [];
    const visibleKeySchools = user.role === 'manager'
        ? keySchools
        : keySchools.filter(s => canAccessSchool(user, s));
    const map = new Map();

    visibleKeySchools.forEach(s => {
        map.set(s.key, {
            key: s.key,
            schoolId: s.schoolId || '',
            province: s.province || '',
            city: s.city || '',
            district: s.district || '',
            school: s.school || '',
            owner: s.owner || '',
            source: '重点校清单',
            classes: new Set(),
            grades: new Map(),
            weeks: new Map()
        });
    });
    const schoolNameToKey = new Map(visibleKeySchools.filter(s => s.school).map(s => [s.school, s.key]));

    const globalLatestWeek = [...new Set(records.map(r => r.weekStartDate || '').filter(Boolean))].sort().pop() || '';

    records.forEach(r => {
        const identity = schoolIdentity(r);
        const key = map.has(identity) ? identity : schoolNameToKey.get(getSchoolName(r)) || identity || schoolKey(r);
        if (!map.has(key)) return;
        const g = map.get(key);
        g.classes.add(getClassId(r) || r['班级名称'] || `${r['学校名称']}-${r['年级'] || ''}`);
        const gradeName = r['年级'] || '未填写年级';
        if (!g.grades.has(gradeName)) g.grades.set(gradeName, []);
        g.grades.get(gradeName).push(r);
        const weekKey = r.weekStartDate || r.weekDisplay || '未识别周次';
        if (!g.weeks.has(weekKey)) {
            g.weeks.set(weekKey, {
                startDate: r.weekStartDate || '',
                display: r.weekDisplay || weekKey,
                assignments: 0,
                completionSum: 0,
                completionCount: 0,
                paid: 0,
                trial: 0,
                students: 0,
                classes: new Set()
            });
        }
        const w = g.weeks.get(weekKey);
        w.assignments += toNumber(r['布置作业次数']);
        w.completionSum += toNumber(r['作业完成率']) * 100;
        w.completionCount += 1;
        w.paid += toNumber(r['未过期付费学生数']);
        w.trial += toNumber(r['未过期试用学生数']);
        w.students += toNumber(r['总学生数']);
        w.classes.add(getClassId(r) || r['班级名称'] || `${getSchoolName(r)}-${r['年级'] || ''}`);
    });

    return [...map.values()].map(g => {
        const weeks = [...g.weeks.values()].sort((a, b) => String(a.startDate).localeCompare(String(b.startDate)));
        weeks.forEach(w => {
            w.completion = w.completionCount ? w.completionSum / w.completionCount : 0;
            w.classCount = w.classes?.size || 0;
            w.avgAssignments = w.classCount ? w.assignments / w.classCount : 0;
            w.payRate = w.students > 0 ? w.paid / w.students * 100 : 0;
        });
        const gradeRows = [...g.grades.entries()].map(([grade, rows]) => {
            const classIds = new Set(rows.map(r => getClassId(r) || r['班级名称'] || `${grade}-${getSchoolName(r)}`));
            const latestRows = globalLatestWeek ? rows.filter(r => r.weekStartDate === globalLatestWeek) : rows;
            const paid = latestRows.reduce((s, r) => s + toNumber(r['未过期付费学生数']), 0);
            const trial = latestRows.reduce((s, r) => s + toNumber(r['未过期试用学生数']), 0);
            const students = latestRows.reduce((s, r) => s + toNumber(r['总学生数']), 0);
            const assignments = latestRows.reduce((s, r) => s + toNumber(r['布置作业次数']), 0);
            const completion = latestRows.length ? latestRows.reduce((s, r) => s + toNumber(r['作业完成率']) * 100, 0) / latestRows.length : 0;
            const activeClassCount = new Set(latestRows.map(r => getClassId(r) || r['班级名称'] || `${grade}-${getSchoolName(r)}`)).size;
            const paidRate = students > 0 ? (paid / students) * 100 : 0;
            return { grade, classCount: classIds.size, students, paid, trial, paidRate, assignments, avgAssignments: activeClassCount ? assignments / activeClassCount : 0, completion };
        });
        const classRows = [];
        g.grades.forEach((rows, grade) => {
            rows.forEach(r => {
                classRows.push({
                    grade,
                    teacher: r['教师姓名'] || r['老师姓名'] || r['教师'] || '',
                    className: r['班级名称'] || '',
                    classId: getClassId(r),
                    students: toNumber(r['总学生数']),
                    paid: toNumber(r['未过期付费学生数']),
                    trial: toNumber(r['未过期试用学生数']),
                    assignments: toNumber(r['布置作业次数']),
                    completion: toNumber(r['作业完成率']) * 100,
                    weekDisplay: r.weekDisplay || r.weekStartDate || ''
                });
            });
        });
        const latest = globalLatestWeek && g.weeks.has(globalLatestWeek)
            ? g.weeks.get(globalLatestWeek)
            : { completion: 0, paid: 0, trial: 0, students: 0, assignments: 0, classCount: 0, avgAssignments: 0, payRate: 0 };
        const payRate = latest.students > 0 ? latest.paid / latest.students * 100 : 0;
        const status = payRate > 20 ? '付费校' : (payRate < 20 && latest.students > 100) ? '试用校' : '未试用校';
        const chargeGrades = gradeRows.filter(row => row.paidRate > 50).map(row => shortGrade(row.grade));
        return {
            key: g.key,
            schoolId: g.schoolId || '',
            province: g.province,
            city: g.city,
            district: g.district,
            school: g.school,
            owner: g.owner,
            classCount: g.classes.size,
            status,
            latest,
            weeks,
            gradeRows,
            classRows,
            chargeGrades,
            globalLatestWeek,
            progress: db.progress[g.key] || { daily: {}, managerReplies: [] }
        };
    });
}

async function handleApi(req, res, url) {
    if (url.pathname === '/api/login' && req.method === 'POST') {
        const body = await readBody(req);
        const db = readDb();
        const user = [ADMIN_USER, ...(db.subAccounts || [])].find(u => u.username === body.username && u.password === body.password);
        if (!user) return sendJson(res, 401, { error: '登录失败：账号或密码错误' });
        const token = crypto.randomBytes(24).toString('hex');
        sessions.set(token, user.username);
        return sendJson(res, 200, { token, user: { username: user.username, role: user.role, name: user.name || user.username, provinces: user.provinces || [] } });
    }

    if (url.pathname === '/api/me' && req.method === 'GET') {
        const user = requireUser(req, res);
        if (!user) return;
        return sendJson(res, 200, { user });
    }

    if (url.pathname === '/api/import' && req.method === 'POST') {
        const user = currentUser(req) || { username: 'manager', role: 'manager', name: '销售管理者' };
        if (user.role !== 'manager') return sendJson(res, 403, { error: '仅管理者可操作' });
        const body = await readBody(req);
        const meta = parseFilename(body.filename || '');
        const records = (body.records || []).map(r => ({ ...r, ...meta, importFilename: body.filename || '' }));
        const db = readDb();
        db.records = db.records.filter(r => r.importFilename !== body.filename);
        db.records.push(...records);
        db.imports = db.imports.filter(i => i.filename !== body.filename);
        db.imports.push({ filename: body.filename || '未命名文件', rows: records.length, uploadedAt: new Date().toISOString(), by: user.username });
        writeDb(db);
        return sendJson(res, 200, { ok: true, rows: records.length });
    }

    if (url.pathname === '/api/dashboard-sync' && req.method === 'POST') {
        const user = requireManager(req, res);
        if (!user) return;
        const body = await readBody(req);
        const db = readDb();
        db.records = Array.isArray(body.records) ? body.records : [];
        db.imports = Array.isArray(body.imports) ? body.imports : [];
        writeDb(db);
        return sendJson(res, 200, { ok: true, rows: db.records.length, imports: db.imports.length });
    }

    if (url.pathname === '/api/key-schools' && req.method === 'POST') {
        const user = currentUser(req) || { username: 'manager', role: 'manager', name: '销售管理者' };
        if (user.role !== 'manager') return sendJson(res, 403, { error: '仅管理者可操作' });
        const body = await readBody(req);
        const rows = Array.isArray(body.records) ? body.records : [];
        const seen = new Set();
        const keySchools = rows.map((r, idx) => {
            const schoolId = getSchoolId(r);
            const school = getSchoolName(r);
            const key = schoolId || school;
            if (!key || seen.has(key)) return null;
            seen.add(key);
            return {
                key,
                schoolId,
                school,
                province: getProvince(r),
                city: getCity(r),
                district: getDistrict(r),
                owner: getOwner(r),
                rowIndex: idx + 1
            };
        }).filter(Boolean);
        const db = readDb();
        db.keySchools = keySchools;
        db.keySchoolImports = [{
            filename: body.filename || '重点校清单.xlsx',
            rows: keySchools.length,
            uploadedAt: new Date().toISOString(),
            by: user.username
        }];
        writeDb(db);
        return sendJson(res, 200, { ok: true, rows: keySchools.length });
    }

    if (url.pathname === '/api/schools' && req.method === 'GET') {
        const user = currentUser(req) || { username: 'manager', role: 'manager', name: '销售管理者' };
        const db = readDb();
        const schools = aggregateSchools(db.records, db, user);
        return sendJson(res, 200, {
            schools,
            imports: db.imports || [],
            keySchoolImports: db.keySchoolImports || [],
            subAccounts: db.subAccounts || []
        });
    }

    if (url.pathname === '/api/progress' && req.method === 'POST') {
        const user = requireUser(req, res);
        if (!user) return;
        const body = await readBody(req);
        const db = readDb();
        const school = (db.keySchools || []).find(s => s.key === body.schoolKey);
        if (!school) return sendJson(res, 404, { error: '学校不存在' });
        if (user.role === 'sales' && !canAccessSchool(user, school)) return sendJson(res, 403, { error: '只能填写所属省份学校' });
        const prev = db.progress[body.schoolKey] || { daily: {}, managerReplies: [] };
        const date = String(body.date || '').trim() || new Date().toISOString().slice(0, 10);
        const text = String(body.text || body.note || '').trim();
        prev.daily = prev.daily || {};
        prev.daily[date] = { text, updatedAt: new Date().toISOString(), by: user.username };
        db.progress[body.schoolKey] = prev;
        writeDb(db);
        return sendJson(res, 200, { ok: true, progress: db.progress[body.schoolKey] });
    }

    if (url.pathname === '/api/reply' && req.method === 'POST') {
        const user = requireManager(req, res);
        if (!user) return;
        const body = await readBody(req);
        const db = readDb();
        const prev = db.progress[body.schoolKey] || { daily: {}, managerReplies: [] };
        const reply = String(body.reply || '').trim();
        prev.managerReplies = prev.managerReplies || [];
        if (reply) {
            const replyId = String(body.replyId || '').trim();
            const index = replyId
                ? prev.managerReplies.findIndex((item, i) => String(item.id || i) === replyId)
                : -1;
            if (index >= 0) {
                prev.managerReplies[index] = { ...prev.managerReplies[index], id: prev.managerReplies[index].id || replyId, text: reply, updatedAt: new Date().toISOString(), by: user.username };
            } else {
                prev.managerReplies.push({ id: `${Date.now()}`, text: reply, date: String(body.date || '').trim() || new Date().toISOString().slice(0, 10), progressDate: String(body.progressDate || ''), createdAt: new Date().toISOString(), by: user.username });
            }
        }
        db.progress[body.schoolKey] = prev;
        writeDb(db);
        return sendJson(res, 200, { ok: true, progress: db.progress[body.schoolKey] });
    }

    if (url.pathname === '/api/subaccounts' && req.method === 'GET') {
        const user = requireManager(req, res);
        if (!user) return;
        const db = readDb();
        return sendJson(res, 200, { subAccounts: db.subAccounts || [] });
    }

    if (url.pathname === '/api/subaccounts' && req.method === 'POST') {
        const user = requireManager(req, res);
        if (!user) return;
        const body = await readBody(req);
        const username = String(body.username || '').trim();
        const password = String(body.password || '');
        if (!username || !password) return sendJson(res, 400, { error: '请填写账号和密码' });
        if (username === ADMIN_USER.username) return sendJson(res, 400, { error: '不能覆盖管理者总账号' });
        const db = readDb();
        const provinces = Array.isArray(body.provinces) ? body.provinces.map(String) : (body.province ? [String(body.province)] : []);
        const account = { username, password, role: body.role === 'manager' ? 'manager' : 'sales', name: username, provinces };
        db.subAccounts = (db.subAccounts || []).filter(a => a.username !== username);
        db.subAccounts.push(account);
        writeDb(db);
        return sendJson(res, 200, { ok: true, subAccounts: db.subAccounts });
    }

    if (url.pathname.startsWith('/api/subaccounts/') && req.method === 'DELETE') {
        const user = requireManager(req, res);
        if (!user) return;
        const username = decodeURIComponent(url.pathname.split('/').pop());
        const db = readDb();
        db.subAccounts = (db.subAccounts || []).filter(a => a.username !== username);
        writeDb(db);
        return sendJson(res, 200, { ok: true, subAccounts: db.subAccounts });
    }

    sendJson(res, 404, { error: 'API 不存在' });
}

function serveStatic(req, res, url) {
    const requested = url.pathname === '/' ? '/platform.html' : decodeURIComponent(url.pathname);
    const filePath = path.resolve(ROOT, `.${requested}`);
    if (!filePath.startsWith(ROOT)) {
        res.writeHead(403);
        return res.end('Forbidden');
    }
    fs.readFile(filePath, (err, content) => {
        if (err) {
            res.writeHead(404);
            res.end('404 Not Found');
            return;
        }
        const contentType = mimeTypes[path.extname(filePath)] || 'application/octet-stream';
        res.writeHead(200, { 'Content-Type': contentType });
        res.end(content);
    });
}

const server = http.createServer(async (req, res) => {
    const url = new URL(req.url, `http://${req.headers.host}`);
    try {
        if (url.pathname.startsWith('/api/')) {
            setCorsHeaders(req, res);
            if (req.method === 'OPTIONS') {
                res.writeHead(204);
                res.end();
                return;
            }
            return await handleApi(req, res, url);
        }
        serveStatic(req, res, url);
    } catch (err) {
        sendJson(res, 500, { error: err.message || '服务器错误' });
    }
});

server.listen(PORT, '0.0.0.0', () => {
    ensureDb();
    console.log(`Sales platform running at http://127.0.0.1:${PORT}/platform.html`);
});
