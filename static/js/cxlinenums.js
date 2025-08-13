class LineNumbers {
  constructor(parentElem, siblingElem, isVisible, visid) {
    if (typeof parentElem == 'string') {parentElem = document.getElementById(parentElem);}
    if (typeof siblingElem == 'string') {siblingElem = document.getElementById(siblingElem);}
    this.parentElem = parentElem;
    this.siblingElem = siblingElem;
    this.numLines = this.calculateNumLines();
    this.lineNumbersContainer = this.render();
    this.parentElem.appendChild(this.lineNumbersContainer);
    this.isVisible = isVisible;
    this.setVisible(isVisible);
    if (visid) setVisibilityCallback(this, visid);
  }

  calculateNumLines() {
    const lines = this.siblingElem.textContent.split('\n');
    return lines.length;
  }

  render() {
    const container = document.createElement('div');
    container.className = 'line-numbers';

    for (let i = 1; i <= this.numLines; i++) {
      const lineNumber = document.createElement('div');
      lineNumber.className = 'line-number';
      lineNumber.textContent = i;
      container.appendChild(lineNumber);
    }

    return container;
  }

  setVisible(visible) {
    this.isVisible = visible;
    this.lineNumbersContainer.style.display = visible ? 'block' : 'none';
  }
}

// helper function for line number visibility
function setVisibilityCallback(lineNumbers, visid) {
  document.getElementById(visid).addEventListener('click', () => {
    lineNumbers.setVisible(!lineNumbers.isVisible);
  });
}
// Export the class if using modules
// export default LineNumbers;
