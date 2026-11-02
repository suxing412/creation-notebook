/* Local-only exact byte reconstruction; no analytics, external requests or filesystem API. */
export function validateManifest(m) {
  const a = m?.archive, parts = m?.parts;
  const sha = /^[0-9a-f]{64}$/;
  if (m?.format !== 'exact-zip-byte-parts-v1' || !a || !/^[A-Za-z0-9][A-Za-z0-9._-]*\.zip$/.test(a.name) || !sha.test(a.sha256) || !Number.isSafeInteger(a.bytes) || a.bytes <= 0) throw new Error('原包身份格式不正确');
  if (typeof a.originalPath !== 'string' || a.originalPath.startsWith('/') || a.originalPath.split('/').includes('..')) throw new Error('原始路径格式不正确');
  if (!Array.isArray(parts) || parts.length === 0 || m.partCount !== parts.length) throw new Error('分卷数量不正确');
  let total = 0;
  for (let i = 0; i < parts.length; i++) {
    const p = parts[i];
    if (p.index !== i + 1 || p.file !== `${a.name}.part${String(i + 1).padStart(3, '0')}`) throw new Error('分卷顺序或名称不正确');
    if (!Number.isSafeInteger(p.bytes) || p.bytes <= 0 || p.bytes > 8 * 1024 * 1024 || !sha.test(p.sha256)) throw new Error('分卷身份格式不正确');
    total += p.bytes;
  }
  if (total !== a.bytes) throw new Error('分卷总大小不等于原 ZIP');
  return m;
}

export async function sha256(bytes) {
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, '0')).join('');
}

export async function verifyPart(bytes, p) {
  if (bytes.byteLength !== p.bytes || await sha256(bytes) !== p.sha256) throw new Error(`第 ${p.index} 卷大小或 SHA-256 不匹配；拒绝合并`);
  return bytes;
}

export async function joinVerifiedParts(m, parts) {
  validateManifest(m);
  if (parts.length !== m.parts.length) throw new Error('缺少分卷；拒绝合并');
  const whole = new Uint8Array(m.archive.bytes);
  let offset = 0;
  for (let i = 0; i < parts.length; i++) {
    const bytes = parts[i];
    if (!(bytes instanceof Uint8Array)) throw new Error('缺少分卷；拒绝合并');
    await verifyPart(bytes, m.parts[i]);
    whole.set(bytes, offset);
    offset += bytes.byteLength;
  }
  if (offset !== m.archive.bytes || await sha256(whole) !== m.archive.sha256) throw new Error('整包 SHA-256 不匹配；拒绝生成 ZIP');
  return whole;
}

function bindPage() {
  const root = document.querySelector('[data-archive-manifest]');
  if (!root) return;
  const start = document.querySelector('#start'), cancel = document.querySelector('#cancel'), clear = document.querySelector('#clear'), save = document.querySelector('#save'), status = document.querySelector('#status'), progress = document.querySelector('#progress');
  const retained = new Map();
  let running = false, controller = null, objectURL = null;
  const resetSave = () => { save.hidden = true; save.removeAttribute('href'); if (objectURL) URL.revokeObjectURL(objectURL); objectURL = null; };
  const updateButtons = () => { start.disabled = running; cancel.disabled = !running; clear.disabled = running || retained.size === 0; };
  const abortIfNeeded = () => { if (controller?.signal.aborted) throw new DOMException('Aborted', 'AbortError'); };
  if (!globalThis.isSecureContext || !globalThis.crypto?.subtle) {
    status.textContent = '本环境不支持安全 SHA-256。请在 HTTPS 静态站点打开，或使用下方 Python 离线还原；尚未生成 ZIP。';
    return;
  }
  start.disabled = false;
  start.addEventListener('click', async () => {
    if (running) return;
    running = true; controller = new AbortController(); resetSave(); updateButtons();
    try {
      status.textContent = '读取并校验分卷清单…';
      const manifestURL = new URL(root.dataset.archiveManifest, location.href);
      if (manifestURL.origin !== location.origin) throw new Error('拒绝跨站清单');
      const response = await fetch(manifestURL, { signal: controller.signal, cache: 'no-store', credentials: 'omit', referrerPolicy: 'no-referrer' });
      if (!response.ok) throw new Error(`清单请求失败：HTTP ${response.status}`);
      const raw = await response.arrayBuffer(); abortIfNeeded();
      if (await sha256(raw) !== root.dataset.manifestSha256) throw new Error('清单 SHA-256 不匹配');
      const m = validateManifest(JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(raw))); abortIfNeeded();
      progress.max = m.parts.length; progress.value = retained.size;
      for (const p of m.parts) {
        abortIfNeeded();
        if (retained.has(p.index)) { await verifyPart(retained.get(p.index), p); continue; }
        status.textContent = `下载并校验第 ${p.index} / ${m.parts.length} 卷；已保留 ${retained.size} 卷…`;
        const partURL = new URL(p.file, manifestURL);
        if (partURL.origin !== location.origin) throw new Error('拒绝跨站分卷');
        const partResponse = await fetch(partURL, { signal: controller.signal, cache: 'no-store', credentials: 'omit', referrerPolicy: 'no-referrer' });
        if (!partResponse.ok) throw new Error(`第 ${p.index} 卷请求失败：HTTP ${partResponse.status}`);
        const bytes = new Uint8Array(await partResponse.arrayBuffer()); abortIfNeeded();
        await verifyPart(bytes, p); abortIfNeeded();
        retained.set(p.index, bytes); progress.value = retained.size;
      }
      status.textContent = '全部分卷已校验，正在校验重组 ZIP 的完整 SHA-256…';
      const whole = await joinVerifiedParts(m, m.parts.map(p => retained.get(p.index))); abortIfNeeded();
      objectURL = URL.createObjectURL(new Blob([whole], { type: 'application/zip' }));
      save.href = objectURL; save.download = m.archive.name; save.hidden = false;
      status.textContent = `已重组并通过完整 SHA-256：${m.archive.bytes.toLocaleString()} 字节。请点击“保存已校验 ZIP”；尚不代表文件已经保存到磁盘。`;
      start.textContent = '重新校验';
    } catch (error) {
      resetSave();
      status.textContent = `${error.name === 'AbortError' ? '已取消' : `失败：${error.message}`}。尚未生成可保存 ZIP；本页保留 ${retained.size} 个已校验卷。修复网络或资源后点“继续 / 重试”。`;
      start.textContent = '继续 / 重试';
    } finally { running = false; controller = null; updateButtons(); }
  });
  cancel.addEventListener('click', () => { if (running) { controller.abort(); status.textContent = '正在取消；不会保存未完成的 ZIP…'; cancel.disabled = true; } });
  clear.addEventListener('click', () => { if (!running) { retained.clear(); resetSave(); progress.value = 0; start.textContent = '校验并还原 ZIP'; status.textContent = '已清除本页内存缓存；尚未生成 ZIP。'; updateButtons(); } });
  addEventListener('pagehide', () => { controller?.abort(); resetSave(); });
  addEventListener('pageshow', event => {
    if (event.persisted) {
      resetSave();
      status.textContent = '已返回页面；保存链接已清除。请重新校验，再保存 ZIP；本页仍可复用已校验的分卷。';
      start.textContent = '重新校验';
      updateButtons();
    }
  });
}
if (typeof document !== 'undefined') bindPage();
