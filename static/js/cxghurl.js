window.addEventListener("DOMContentLoaded", async () => {
  const statusDiv = document.querySelector('[data-role="status"]');
  const codeBox = document.querySelector('[data-role="code"]');

  function updateStatus(msg, isError = false) {
    if (statusDiv) {
      statusDiv.textContent = msg;
      statusDiv.style.color = isError ? "red" : "black";
    }
  }

  const params = new URLSearchParams(window.location.search);
  const ghParam = params.get("gh");

  if (!ghParam) {
    //updateStatus("No ?gh= parameter specified.");
    return;
  }

  updateStatus("Forming GitHub path...");

  const [user, repo, branch, ...pathParts] = ghParam.split("/");
  if (!user || !repo || !branch || pathParts.length === 0) {
    updateStatus("❌ Invalid GitHub path format. Use user/repo/branch/path/to/file.py", true);
    return;
  }

  updateStatus("Loading from GitHub...");

  const rawUrl = `https://raw.githubusercontent.com/${user}/${repo}/${branch}/${pathParts.join("/")}`;

  try {
    const resp = await fetch(rawUrl);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const code = await resp.text();
    if (codeBox) codeBox.value = code;
    updateStatus("✅ Code loaded from GitHub.");
    console.log('Code loaded from GitHib');
    const event = new Event('ghCodeLoaded');
    window.dispatchEvent(event);
  } catch (err) {
    updateStatus("❌ Failed to fetch file: " + err.message, true);
  }
});
