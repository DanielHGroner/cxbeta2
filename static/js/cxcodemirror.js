document.addEventListener('DOMContentLoaded', function () {
  var ta = document.getElementById('codeInput');
  if (!ta) return;

  var cm = CodeMirror.fromTextArea(ta, {
    mode: 'python',
    lineNumbers: true,
    lineWrapping: false,
    theme: 'plain',
    indentUnit: 4,
    tabSize: 4,
    indentWithTabs: false,
    extraKeys: {
      Tab: function(cm) { cm.replaceSelection('    '); }
    }
  });

  cm.on('change', function() {
    var v = cm.getValue();
    if (ta.value !== v) {
      ta.value = v;
      ta.dispatchEvent(new Event('input', { bubbles: true }));
    }
  });

  setTimeout(function () {
    cm.setValue(ta.value);
    cm.refresh();
  }, 0);

  window._cm = cm;
});

// after: window._cm = cm;
function setCode(text) {
  const ta = document.getElementById('codeInput');

  if (window._cm) {
    // batch updates for performance
    window._cm.operation(function () {
      window._cm.setValue(text);
      window._cm.setCursor({ line: 0, ch: 0 });
      window._cm.scrollTo(0, 0);
    });
  }

  // keep the underlying <textarea> in sync for existing code paths
  if (ta) {
    ta.value = text;
    // trigger any existing 'input' listeners your app relies on
    ta.dispatchEvent(new Event('input', { bubbles: true }));
  }
}


// ** Error-related

// Track applied marks so we can clear them later
let _errMarks = [];

/** Highlight an error line: line1Based is 1,2,3... */
function markErrorLine(line1Based) {
  if (!window._cm || !Number.isFinite(line1Based)) return;
  const line0 = Math.max(0, line1Based - 1);
  const handle = window._cm.addLineClass(line0, "gutter", "cm-error-lnum");
  _errMarks.push({ handle, where: "gutter", className: "cm-error-lnum" });
}

/** Remove all error highlights */
function clearErrorMarks() {
  if (!window._cm) return;
  _errMarks.forEach(m => window._cm.removeLineClass(m.handle, m.where, m.className));
  _errMarks = [];
}
