
const githubLoader = {
  currentRepo: '',
  defaultBranch: 'main',
  selectedPath: [],
  columnsEl: null,
  repoInputEl: null,
  overlayEl: null,
  dialogEl: null,
  errorLabelEl: null,

  async openDialog() {
    this.columnsEl = document.getElementById('columns');
    this.repoInputEl = document.getElementById('repoInput');
    this.overlayEl = document.getElementById('githubOverlay');
    this.dialogEl = document.getElementById('githubDialog');
    this.errorLabelEl = document.getElementById('repoErrorLabel');

    this.overlayEl.style.display = 'flex';
    this.dialogEl.style.display = 'flex';
    this.columnsEl.innerHTML = '';
    this.errorLabelEl.textContent = '';
    this.selectedPath = [];

    const repoValue = this.repoInputEl.value.trim();
    if (!repoValue.includes('/')) {
      this.errorLabelEl.textContent = 'Please enter repo as username/reponame.';
      return;
    }

    this.currentRepo = repoValue;
    localStorage.setItem('githubRepo', this.currentRepo);

    try {
      const repoInfo = await fetch(`https://api.github.com/repos/${this.currentRepo}`);
      if (!repoInfo.ok) throw new Error('Repo not found.');
      const repoData = await repoInfo.json();
      this.defaultBranch = repoData.default_branch || 'main';
      this.loadDirectory('', 0);
    } catch (err) {
      this.errorLabelEl.textContent = err.message || 'Failed to load repo info.';
    }
  },

  closeDialog(shouldOpen) {
    this.overlayEl.style.display = 'none';
    this.dialogEl.style.display = 'none';

    if (shouldOpen && this.selectedPath.length > 0) {
      const fullPath = this.selectedPath.join('/');
      const fetchURL = `https://raw.githubusercontent.com/${this.currentRepo}/${this.defaultBranch}/${fullPath}`;
      console.log('Repo:', this.currentRepo);
      console.log('Branch:', this.defaultBranch);
      console.log('Path:', fullPath);
      console.log('URL:', fetchURL);

      fetch(fetchURL)
        .then(res => res.ok ? res.text() : Promise.reject('Unable to fetch file.'))
        .then(text => {
          document.getElementById('codeDisplay').value = text;
        })
        .catch(err => alert(err));
    }
  },

  loadDirectory(path, columnIndex) {
    const url = `https://api.github.com/repos/${this.currentRepo}/contents/${path}?ref=${this.defaultBranch}`;
    fetch(url)
      .then(res => {
        if (!res.ok) throw new Error('Invalid user/repo or folder.');
        return res.json();
      })
      .then(items => {
        while (this.columnsEl.children.length > columnIndex) {
          this.columnsEl.removeChild(this.columnsEl.lastChild);
          this.selectedPath.pop();
        }

        const col = document.createElement('div');
        col.className = 'cx-column';

        items
          .filter(item => item.type === 'dir' || item.name.endsWith('.py'))
          .forEach(item => {
            const entry = document.createElement('div');
            entry.className = 'cx-entry';
            entry.textContent = (item.type === 'dir' ? '📁 ' : '📄 ') + item.name;
            entry.onclick = () => {
              Array.from(col.children).forEach(child => child.classList.remove('selected'));
              entry.classList.add('selected');
              this.selectedPath[columnIndex] = item.name;

              if (item.type === 'dir') {
                this.loadDirectory(this.selectedPath.slice(0, columnIndex + 1).join('/'), columnIndex + 1);
              } else {
                while (this.columnsEl.children.length > columnIndex + 1) {
                  this.columnsEl.removeChild(this.columnsEl.lastChild);
                  this.selectedPath.pop();
                }
              }
            };
            col.appendChild(entry);
          });

        this.columnsEl.appendChild(col);
      })
      .catch(err => {
        this.errorLabelEl.textContent = err.message || 'Failed to load directory.';
      });
  },

  restoreRepo() {
    const savedRepo = localStorage.getItem('githubRepo');
    if (savedRepo && document.getElementById('repoInput')) {
      document.getElementById('repoInput').value = savedRepo;
    }
  }
};

window.addEventListener('DOMContentLoaded', () => {
  githubLoader.restoreRepo();
});
