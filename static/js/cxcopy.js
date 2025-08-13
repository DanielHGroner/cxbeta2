const copyButton = document.getElementById('copy-button');
const codeDiv = document.getElementById('code');
const copyMessage = document.getElementById('copy-message');

copyButton.addEventListener('click', () => {
  // Get the text content of the div, removing any HTML tags
  const textToCopy = codeDiv.textContent.trim();

  // Use the Clipboard API to copy the text
  navigator.clipboard.writeText(textToCopy)
    .then(() => {
      copyMessage.classList.add('show');
      setTimeout(() => {
        copyMessage.classList.remove('show');
      }, 1500);  // Adjust this value to control message display time
    })
    .catch(err => {
      console.error('Failed to copy code:', err);
    });
});
