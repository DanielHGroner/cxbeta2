
let currentHelpSpan = null;  // To track current help span

function clearHelp() {
  helpContainer.innerHTML = '';
  helpContainer.style.display = "none";
  currentHelpSpan = null;
}

document.addEventListener("DOMContentLoaded", function() {
    const helpContainer = document.getElementById("help-container");
    const helpSpans = document.querySelectorAll(".help-span");
    let isDragging = false;
    let offsetX, offsetY;
    
    // Display help text when a span is clicked
    helpSpans.forEach(span => {
      //console.log(span);
      span.addEventListener("click", function() {
        const spanId = this.id;
        const helpText = allhelp?.[spanId];        // undefined if no help entry
        console.log(spanId, helpText);
        if (!helpDisplaying) {                     // user turned help off
          clearHelp();
          return;
        }
        if (helpText && helpText !== '-') {        // only render real help
          showHelp(span, helpText);
        } else {
          clearHelp();                              // nothing for this span → hide
        }
      });
    });
  
    // Function to display help text
    function showHelp(span, text) {
      console.log("in showHelp()")
      if (!helpDisplaying) { clearHelp(); return;}
      if (!text || text === '-') { clearHelp(); return;}
      helpContainer.innerHTML = text;
      helpContainer.style.display = "block";
      currentHelpSpan = span;

      // ** initial placement of the help
      const spanRect = span.getBoundingClientRect();
      
      // Calculate the position to place the help container next to the span
      let left = spanRect.right + window.scrollX;
      let top = spanRect.bottom + window.scrollY;

      helpContainer.style.left = left + 'px';
      helpContainer.style.top = top + 'px';

      // ** refine placement of the help, if needed
      // Get the bounding rectangle of the help box
      const rect = helpContainer.getBoundingClientRect();
      // Check if the box is off-screen and adjust position if necessary
      const viewportWidth = window.innerWidth;
      // Adjust if the box is off the right edge
      if (rect.right > viewportWidth) {
          helpContainer.style.left = `${viewportWidth - rect.width}px`;
      }
    }
  
    // Function to handle mouse down event on help container
    helpContainer.addEventListener("mousedown", function(event) {
      isDragging = true;
      offsetX = event.clientX - helpContainer.getBoundingClientRect().left;
      offsetY = event.clientY - helpContainer.getBoundingClientRect().top;
    });
  
    // Function to handle mouse move event
    document.addEventListener("mousemove", function(event) {
      if (isDragging) {
        const newX = event.clientX - offsetX;
        const newY = event.clientY - offsetY;
        helpContainer.style.left = `${newX}px`;
        helpContainer.style.top = `${newY}px`;
      }
    });
  
    // Function to handle mouse up event
    document.addEventListener("mouseup", function() {
      isDragging = false;
    });  
  });
  