function adjustArrowLayerHeight() {
    //console.log('in adjustArrowLayerHeight()')
    const arrowLayer = document.getElementById("svgElem");
    if (arrowLayer) {
        arrowLayer.style.height = document.body.scrollHeight + "px";
    }
}

// Call once initially
adjustArrowLayerHeight();

// Update on resize
window.addEventListener("resize", adjustArrowLayerHeight);


class ArrowTurn {
    constructor(x1, y1, x2, y2, colorv, colorh, text) {
        this.x1 = x1;
        this.y1 = y1;
        this.x2 = x2;
        this.y2 = y2;
        this.colorv = colorv;
        this.colorh = colorh;
        this.text = text;
        this.visible = true;
    }

    draw(svgElement) {
        if (this.visible) {
            // Create the vertical line
            this.verticalLine = this.createLine(this.x1, this.y1, this.x1, this.y2, this.colorv, 2);
            svgElement.appendChild(this.verticalLine);

            // Create horizontal tail
            // TODO: this could be an option
            const xtail = this.x1 + (this.x2-this.x1) / 2
            this.horizontalLine0 = this.createLine(this.x1, this.y1, xtail, this.y1, this.colorv, 2);
            svgElement.appendChild(this.horizontalLine0);

            // Create the horizontal line
            this.horizontalLine = this.createLine(this.x1, this.y2, this.x2, this.y2, this.colorh, 2);
            svgElement.appendChild(this.horizontalLine);

            // Create the arrowhead
            this.arrowHead = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
            const arrowPoints = `${this.x2},${this.y2-5} ${this.x2+10},${this.y2} ${this.x2},${this.y2+5}`;
            this.arrowHead.setAttribute("points", arrowPoints);
            this.arrowHead.setAttribute("fill", this.colorh);
            svgElement.appendChild(this.arrowHead);

            // create the text
            if (this.text) {
                this.textElem = document.createElementNS("http://www.w3.org/2000/svg", "text");
                this.textElem.setAttribute("x", this.x1+15);
                this.textElem.setAttribute("y", this.y1+3);
                this.textElem.setAttribute("font-size", 12);
                this.textElem.textContent = this.text;
                svgElement.appendChild(this.textElem);
            }
            else {
                this.textElem = null;
            }
        }
    }

    createLine(x1, y1, x2, y2, stroke, strokeWidth) {
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", x1);
        line.setAttribute("y1", y1);
        line.setAttribute("x2", x2);
        line.setAttribute("y2", y2);
        line.setAttribute("stroke", stroke);
        line.setAttribute("stroke-width", strokeWidth);
        return line;
    }

    setVisible(visible) {
        this.visible = visible;
        if (this.verticalLine && this.horizontalLine && this.arrowHead) {
            const display = this.visible ? 'block' : 'none';
            this.verticalLine.style.display = display;
            this.horizontalLine.style.display = display;
            this.arrowHead.style.display = display;
            if (this.textElem) {
                this.textElem.style.display = display;
            }
        }
    }
}

class ArrowBetween {
    constructor(elem1, elem2, x1, width, colorv, colorh, text) {
        this.elem1 = elem1;
        this.elem2 = elem2;
        this.width = width;
        this.colorv = colorv;
        this.colorh = colorh;
        this.text = text;

        const rect1 = elem1.getBoundingClientRect();
        const rect2 = elem2.getBoundingClientRect();

        /* const x1 = rect1.left - width - 15; */
        const y1 = rect1.top + window.scrollY + rect1.height / 2;
        const y2 = rect2.top + window.scrollY + rect2.height / 2;
        const x2 = x1 + width;

        this.arrowTurn = new ArrowTurn(x1, y1, x2, y2, colorv, colorh, text);
    }

    draw(svgElement) {
        this.arrowTurn.draw(svgElement);
    }

    setVisible(visible) {
        this.arrowTurn.setVisible(visible);
    }
}
