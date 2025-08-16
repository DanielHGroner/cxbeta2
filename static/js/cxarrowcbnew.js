// draw arrow(s) when specified statement is clicked on

// requires cx-hilitable as class
const cxHilitables = document.querySelectorAll(".cx-hilitable");
// requires svgElem as id for svg element
const svgElem = document.getElementById("svgElem");

console.log("*** in cxarrowcbnew.js");
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

// install the click callbacks
cxHilitables.forEach(span => {
    console.log("*** in cxHilitables.forEach()", span);
    span.addEventListener("click", function(event) {
        console.log("*** in cxHilitables.forEach() addEventListener()", this.id);
        // clear the prior arrow(s), if any
        svgElem.innerHTML = "";
        // remove this code after testing
        //hilite(this);
        // get the flows for this element
        flow_items = allflows[this.id];
        //console.log(toarrows);
        if (flow_items) { // any flows associated with the clicked on element?
            //const x1 = 5; // start of arrow x axis location
            // const w = 15; // length of landscape arrow (pointing to code)
            for (const flow_item of flow_items) { // for each of the flows for this statement
                var x1 = 9;
                var w = 15; // length of landscape arrow (pointing to code)
                // handle from/to flows                
                if ('stmt_to' in flow_item) {
                    // handle from/to flow(s)
                    color = 'black'; // default color
                    text = null; // default text
                    stroke_pattern = null;
                    // TODO - implement different colors/styling for different types; 
                    //        for now blue for call/return; gray for ambiguous return
                    if (flow_item['type'] == 'call') {
                        color = 'blue';
                        stroke_pattern = "5";
                        x1 = 3;
                    }
                    // if 'return_type' set, then it's a return statement
                    if ('return_type' in flow_item) {
                        color = 'blue';
                        stroke_pattern = "5";
                        x1 = 3;
                    }
                    // separate styling for raise (below uses pink for ambiguous raise to caller)
                    if (flow_item['is_raise']) {
                        color = 'red';
                        text = '⚡';
                    }
                    console.log("generating from/to arrow(s):", flow_item, x1, w);
                    //console.log("generating from/to arrow(s): stroke_pattern", stroke_pattern);
                    // handle list of stmt_to that comes with return flows
                    // TODO - later may get list with case/match
                    const stmt_to = flow_item['stmt_to'];
                    // handle array of stmt_to - initially this is for return flows
                    if (Array.isArray(stmt_to)) {
                        // styling for ambiguous return path (gray or pink)
                        if ('return_type' in flow_item && stmt_to.length > 1) {
                            color = 'gray'; 
                            if (flow_item['is_raise']) color = 'pink';
                        }
                        // draw an array for each possible return path
                        for (const stmt_to_item of stmt_to) {
                            const fromStmt = document.getElementById(String(stmt_to_item));
                            if (fromStmt) {
                                const arrow = new ArrowBetween(this, fromStmt, x1, w, color, color, text, stroke_pattern);
                                arrow.draw(svgElem);
                            }
                        }
                    // handle simple from/to pair
                    } else {
                        const fromStmt = document.getElementById(String(flow_item['stmt_to']));
                        if (fromStmt) {
                            // text = null;
                            type = flow_item['type'];
                            // handle break and continue - add ! and styling
                            if (type == 'continue' || type == 'break') {
                                 color = 'orange';
                                 text = '!';
                            }
                            const arrow = new ArrowBetween(this, fromStmt, x1, w, color, color, text, stroke_pattern);
                            arrow.draw(svgElem);
                        }
                    }
                }
                // handle conditonal (true/false) flows
                else if ('stmt_to_true' in flow_item && 'stmt_to_false' in flow_item) { // true/false flow outcomes)
                    console.log("generating 2 arrows (conditional statement):", flow_item);
                    const fromStmt1 = document.getElementById(String(flow_item['stmt_to_true']));
                    if (fromStmt1) {
                        const arrow1 = new ArrowBetween(this, fromStmt1, x1, w, "black", "limegreen", "?");
                        arrow1.draw(svgElem);
                    }
                    const fromStmt2 = document.getElementById(String(flow_item['stmt_to_false']));
                    if (fromStmt2) {
                        const arrow2 = new ArrowBetween(this, fromStmt2, x1, w, "black", "red");
                        arrow2.draw(svgElem);
                    }
                }
            }
        }
    });
})