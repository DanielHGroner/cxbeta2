// draw arrows when specified statements are clicked on

// requires cx-hilitable as class
const cxStatementsa = document.querySelectorAll(".cx-hilitable");
// requires svgElem as id for svg element
const svgElem = document.getElementById("svgElem");

//console.log("*** in cxarrowcb.js");
//console.log(cxStatements);

// remove after testing
/*
lastHiliteElem = null;
function hilite(e) {
    if (lastHiliteElem) {
      lastHiliteElem.style.backgroundColor  = "white";
    }
    e.style.backgroundColor = "yellow";
    lastHiliteElem = e;
}
*/

// intall the click callback
cxStatementsa.forEach(span => {
    //console.log("*** in cxStatements.forEach()", span);
    span.addEventListener("click", function(event) {
        //console.log("*** in cxStatements.forEach() addEventListener()", this.id);
        // clear the prior arrow(s), if any
        svgElem.innerHTML = "";
        // remove this code after testing
        //hilite(this);
        // get the arrows for this element
        toarrows = allarrows[this.id];
        //console.log(toarrows);
        if (toarrows) { // if there are any arrows associated with the clicked on element
            const x1 = 5;
            const len = 15;
            if (typeof toarrows == "string") { // one "to" arrow (as string)
                //console.log("1 arrow:", toarrows);
                const fromStmt = document.getElementById(toarrows);
                if (fromStmt) {
                    const arrow = new ArrowBetween(this, fromStmt, x1, len, "black", "black");
                    arrow.draw(svgElem);
                }
            }
            else if (toarrows.length == 1) { // one "to" arrow (as list of one)
                //console.log("1 arrow:", toarrows[0]);
                const fromStmt = document.getElementById(toarrows[0]);
                if (fromStmt) {
                    const arrow = new ArrowBetween(this, fromStmt, x1, len, "black", "black");
                    arrow.draw(svgElem);
                }
            }
            else if (toarrows.length == 2) { // two "to" arrows (as list of two)
                //console.log("2 arrows:", toarrows[0], toarrows[1]);
                const fromStmt1 = document.getElementById(toarrows[0]);
                if (fromStmt1) {
                    const arrow1 = new ArrowBetween(this, fromStmt1, x1, len, "black", "limegreen", "?");
                    arrow1.draw(svgElem);
                }
                const fromStmt2 = document.getElementById(toarrows[1]);
                if (fromStmt2) {
                    const arrow2 = new ArrowBetween(this, fromStmt2, x1, len, "black", "red");
                    arrow2.draw(svgElem);
                }
            }
        }
    });
})