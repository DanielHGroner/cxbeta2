// stage 1 - find all defining lines
console.log('In cxcollapse.js');
console.log(allscopes);

// ADD: helper to place caret just before the trailing newline inside a line span
function appendCaretBeforeNewline(lineEl, btn) {
  const last = lineEl.lastChild;
  if (last && last.nodeType === Node.TEXT_NODE) {
    const m = /([\s\S]*?)(\r?\n)$/.exec(last.data); // split off trailing \n or \r\n
    if (m) {
      last.data = m[1];                              // strip newline from text node
      lineEl.appendChild(btn);                       // insert caret
      lineEl.appendChild(document.createTextNode(m[2])); // restore newline
      return;
    }
  }
  // Fallback: no trailing newline text node; just append at end
  lineEl.appendChild(btn);
}

(function () {
  // --- helpers: line lookup
  const rows = Array.from(document.querySelectorAll('.cx_srcline[id], .cx_srcline[data-line]'));
  const lineMap = new Map();
  const numFromRow = el => {
    const id = el.id || '';
    if (id) return parseInt(id, 10);
    const dl = el.getAttribute('data-line');
    return dl ? +dl : NaN;
  };
  for (const el of rows) {
    const n = numFromRow(el);
    if (Number.isFinite(n)) lineMap.set(n, el);
  }
  const rowFor = n => lineMap.get(n) || null;

  // --- normalize scope numbers & detect if body exists
  for (const [k, m] of Object.entries(allscopes)) {
    m._def  = +k;
    m._hEnd = +m.header_end_line;
    m._last = +m.last_stmt_line;
    m._hasBody = m._last > m._hEnd;
  }

  // --- inject toggles on def lines
  for (const [k, m] of Object.entries(allscopes)) {
    const el = rowFor(m._def);
    if (!el) continue;
    if (el.querySelector('.cx-toggle')) continue;        // idempotent
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'cx-toggle';
    btn.setAttribute('aria-expanded', 'true');
    //.title = {Collapse/Expand ${m.kind} ${m.qname || ''}.trim();
    if (!m._hasBody) { btn.disabled = true; btn.title = 'No body to collapse'; }
    //el.prepend(btn);
    appendCaretBeforeNewline(el, btn);
  }

  // --- collapse state + apply
  const collapsed = new Set();

  function apply() {
    for (const [k, m] of Object.entries(allscopes)) {
      const open = !collapsed.has(k);
      const header = rowFor(m._def);
      const btn = header && header.querySelector('.cx-toggle');
      if (btn && !btn.disabled) btn.setAttribute('aria-expanded', String(open));

      // Hide/show BODY lines: (header_end_line, last_stmt_line]
      for (let n = m._hEnd + 1; n <= m._last; n++) {
        const r = rowFor(n);
        if (r) r.classList.toggle('cx-hidden', !open);
      }
    }
  }

  // --- click to toggle
  document.addEventListener('click', (e) => {
    const t = e.target.closest('.cx-toggle');
    if (!t) return;
    const row = t.closest('.cx_srcline');
    if (!row) return;
    const defLine = String(parseInt(row.id || row.getAttribute('data-line'), 10));
    if (!(defLine in allscopes)) return;
    if (collapsed.has(defLine)) collapsed.delete(defLine); else collapsed.add(defLine);
    apply();
    refreshAll(e); // coordinate for other features
  });

  // expose tiny API for debugging
  window.cxCollapse = {
    collapse: (n) => { collapsed.add(String(n)); apply(); },
    expand:   (n) => { collapsed.delete(String(n)); apply(); },
    expandAll: () => { collapsed.clear(); apply(); },
    _state: () => ({ collapsed: Array.from(collapsed) })
  };

  // initial render (all expanded)
  apply();
})();
