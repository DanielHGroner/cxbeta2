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
        const helpText = allhelp?.[spanId] || '-'; // for no help, mark as '-'
        console.log(spanId, helpText);
        if (helpText) {
          showHelp(span, helpText);
        }
      });
    });
  
    // Function to display help text
    function showHelp(span, text) {
      console.log("in showHelp()")
      helpContainer.innerHTML = text || "No help text available.";
      if (helpDisplaying)
         helpContainer.style.display = "block";
      else
         helpContainer.style.display = "none";

      // ** initial placement of the help
      const spanRect = span.getBoundingClientRect();
      
      // Calculate the position to place the help container next to the span
      let leftOffset = spanRect.right + window.scrollY;
      let topOffset = spanRect.bottom;
      //console.log(leftOffset, topOffset);

      helpContainer.style.left = `${leftOffset}px`;
      helpContainer.style.top = `${topOffset}px`;

      // ** refine placement of the help, if needed
      // Get the bounding rectangle of the help box
      const rect = helpContainer.getBoundingClientRect();
      // Check if the box is off-screen and adjust position if necessary
      const viewportWidth = window.innerWidth;
      // Adjust if the box is off the right edge
      if (rect.right > viewportWidth) {
          helpContainer.style.left = `${viewportWidth - rect.width}px`;
      }
      

      // empty help
      if (text == '-' || text == '') {helpContainer.style.display = "none";}
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
  
    // superceeded by show/hide toggle feature
    // Hide help container when clicked outside
    /*
    document.addEventListener("click", function(event) {
      //console.log('clicked outside current statement')
      let clickedSpan = false;
      helpSpans.forEach(span => {
        if (span.contains(event.target)) {
          clickedSpan = true;
        }
      });
  
      if (!helpContainer.contains(event.target) && !clickedSpan) {
        helpContainer.style.display = "none";
      }
    });*/
  });
  