function saveGeminiKey() {
    const key = document.getElementById("aihelp-apikeyInput").value.trim();
    localStorage.setItem("cxGeminiApiKey", key);
    alert("API key saved locally.");
}

function getGeminiKey() {
    return localStorage.getItem("cxGeminiApiKey") || "";
}

function prefillApiKeyField() {
    const storedKey = getGeminiKey();
    if (storedKey) {
        const input = document.getElementById("aihelp-apikeyInput");
        if (input) input.value = storedKey;
    }
}

function prefillApiKeyField() {
  const storedKey = localStorage.getItem("cxGeminiApiKey");
  const input = document.getElementById("aihelp-apikeyInput");
  if (input && storedKey) {
    input.value = storedKey;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  prefillApiKeyField();
  // other startup logic if needed
});
