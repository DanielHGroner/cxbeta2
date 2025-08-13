// Support hiliting of a selected element, and its related elements
const cxStatements = document.querySelectorAll(".cx-hilitable");

let currentHighlightedSpan = null;  // To track currently highlighted span
let currentHighlightedSpans2 = []; // To track mapped-to span2s
let currentHighlightedSpans3 = []; // To track mapped-to span3s

cxStatements.forEach(span => {
  span.addEventListener("click", function(event) {
    // Remove highlight from any previously highlighted span
    if (currentHighlightedSpan) {
      currentHighlightedSpan.classList.remove("cx-hilited");
    }
    // Remove highlight from all previously mapped-to hilited2 spans
    currentHighlightedSpans2.forEach(elem => {
       elem.classList.remove("cx-hilited2");
    });
    currentHighlightedSpans2 = [];
    // Remove highlight from all previously mapped-to hilited3 spans
    currentHighlightedSpans3.forEach(elem => {
      elem.classList.remove("cx-hilited3");
   });
   currentHighlightedSpans3 = [];

    // remove the actions (if any) from the variables table
    currentActionCells.forEach(elem => {
      elem.innerHTML = "";
    });
    currentActionCells = [];
  
    // Highlight the clicked span
    this.classList.add("cx-hilited");
    currentHighlightedSpan = this;

    // Hilite the mapped-to highlight 2s
    //console.log(this.id);
    //console.log(allhilite2[this.id]);
    tohilite2 = allhilite2[this.id];
    if (tohilite2) {
      tohilite2.forEach(spanid => {
        //console.log(spanid);
        first = spanid.charAt(0);
        // TODO: is there a more general way to do this?
        if (first == '<' || first == '>' || first =='*') {
          spanid = spanid.slice(1);
          //console.log(first, spanid);
        }
        else {
          first = '';
        }
        const elem = document.getElementById(spanid);
        elem.classList.add("cx-hilited2");
        currentHighlightedSpans2.push(elem); // keep track, so they can be un-hilited later
        // TODO - is there a more general way todo this?
        if (first != '') {displayAction(elem, first)}
      });
    }

    // hilite the mapped-to hilite 3s
    tohilite3 = allhilite3[this.id];
    if (tohilite3) {
      tohilite3.forEach(spanid => {
        const elem = document.getElementById(spanid);
        elem.classList.add("cx-hilited3");
        currentHighlightedSpans3.push(elem);
      });
    }

    // Log the ID of the clicked span element
    //console.log("Clicked Span ID:", this.id);
  });
});

let currentActionCells = [];

// this is hard-coded to set the cell 2 to the left
// TODO: is there a more general (convenient) way to support set/get action display?
function displayAction(elem, c) { 
  //console.log('*** Entering displayAction');
  //console.log(elem, c);
  elem0 = elem.parentElement; // move from variable span to it <td> parent
  elem1 = elem0.previousElementSibling; // move over to the left 2x
  elem2 = elem1.previousElementSibling;
  elem2.innerHTML = actionMap(c); // indicate the action
  currentActionCells.push(elem2); // record the <td> as having an action (for later clear)
}

// map the single char indicators to the displayed string
// TODO - are there better action indicators, e.g., unicode or pictures?
function actionMap(c) {
  if (c == '<') { return '<-';}
  if (c == '>') { return '->';}
  if (c == '*') { return '<->';}
  return '';
}
