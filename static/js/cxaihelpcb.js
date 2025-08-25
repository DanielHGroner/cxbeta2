    async function fetchAndSetAiHelp() {
        // change to get from sessionStorage
        //const sourceCode = document.getElementById('source').value;
        // TODO - if session storage is not defined, can error out here
        const sourceCode = sessionStorage.getItem("cxSourceCode") || "";

        // review/adjust each id
        const options = {
            apiProvider: document.getElementById('aihelp-provider')?.value || "dummy",
            modelName: document.getElementById('aihelp-modelName')?.value || "gemini-2.5-flash-lite",
            includeLong: document.getElementById('aihelp-includeLong')?.checked,
            spokenLanguage: document.getElementById('aihelp-language')?.value || "english",
            dryrun: document.getElementById('aihelp-dryrun')?.checked ?? true,
            apikey: document.getElementById('aihelp-apikeyInput')?.value || ""
        };
        console.log("Submitting to /aihelp with options:")
        console.table(options);

        const aihelp_button = document.getElementById("aihelp-button");
        const aihelp_status = document.getElementById("aihelp-status");
        aihelp_button.disabled = true;
        aihelp_status.textContent = "🐶🗞️ Fetching AI Help...";

        try {
            //document.querySelector("button").disabled = true;
            const result = await requestAiHelp(sourceCode, options);
            //document.querySelector("button").disabled = false;
            console.log("returned from requestAiHelp; result=", result);
            // status message

            // Raw response
            //document.getElementById("response").textContent = JSON.stringify(result, null, 2);

            // Parsed help (into allhelp format)
            // check if this is going into the global variable
            console.log("calling convertAiHelpDataToAllHelp");
            allhelp = convertAiHelpDataToAllHelp(result.data, options.includeLong);
            console.log("returned from convertAiHelpDataToAllHelp; allhelp=", allhelp);

            //document.getElementById("parsed").textContent = JSON.stringify(allhelp, null, 2);
            refreshHelp();

            aihelp_status.textContent = "✔️ Help loaded";

        } catch (err) {
            // TODO: add popup or status message
            aihelp_status.textContent = "❌ Error when getting Help";
            console.log('fetchAndSetAiHelp() - exception:')
            console.log(err)
            //document.querySelector("button").disabled = false;
            //document.getElementById("response").textContent = "❌ Error: " + err.message;
            //document.getElementById("parsed").textContent = "";
        }
        aihelp_button.disabled = false;

    }
