class Color {
    constructor(r, g, b) {
        this.r = r;
        this.g = g;
        this.b = b;
    }

    static fromHex(hex) {
        hex = hex.replace("#", "");
        return new Color(
            parseInt(hex.slice(0, 2), 16),
            parseInt(hex.slice(2, 4), 16),
            parseInt(hex.slice(4, 6), 16)
        );
    }

    lerp(other, t) {
        return new Color(
            Math.round(this.r + (other.r - this.r) * t),
            Math.round(this.g + (other.g - this.g) * t),
            Math.round(this.b + (other.b - this.b) * t)
        );
    }

    toHex() {
        let r = this.r.toString(16).padStart(2, '0');
        let g = this.g.toString(16).padStart(2, '0');
        let b = this.b.toString(16).padStart(2, '0');
        return `#${r}${g}${b}`;
    }
}

const SWAPPING_ELEMENT_COLOR = new Color(80, 255, 80);
const GREATER_ELEMENT_COLOR = new Color(255, 80, 80);
const LESSER_ELEMENT_COLOR = new Color(80, 80, 255);
const HIGHLIGHT_COLOR = new Color(255, 255, 255);
const DEFAULT_ELEMENT_COLOR = Color.fromHex("#c4c8db");
const PIVOT_ELEMENT_COLOR = new Color(255, 160, 80);
const HIGHLIGHT_STRENGTH = 0.75;

const MAX_BORDER_RADIUS = 16;
const TOTAL_HEIGHT_PX = 200;
const TOTAL_WIDTH_PX = 2000;

let bar_width_memo = {};     // same semantics as Python

function assert(condition, message) { // functions like the lua 'assert' function
    if (!condition) {
        console.error(message || "Assertion failed! (No message provided)");
    }
    return condition;
}

function getHtmlSrc(data) {

    const arr = data.arr;
    const length = arr.length;

    let borderRadius = MAX_BORDER_RADIUS;

    // Try cached width
    let widthPerBar = bar_width_memo[length] || borderRadius * 2;

    // While width is too small, reduce border radius
    while (widthPerBar <= borderRadius * 2) {
        borderRadius = Math.floor(borderRadius / 2);
        widthPerBar = Math.max(
            Math.floor((TOTAL_WIDTH_PX - borderRadius * (length + 2)) / Math.max(length, 1)),
            1
        );
    }

    // Cache the result
    bar_width_memo[length] = widthPerBar;

    // Build the main container div
    let html = `<div style="display:flex;justify-content:center;align-items:flex-end;height:${TOTAL_HEIGHT_PX}px;gap:${borderRadius}px;">`;

    // Compute height scaling
    let maxVal = Math.max(Math.max(...arr, 4), 4);
    let heightFactor = 1 / maxVal;

    let pivotVal = null;
    if (data.pv !== null && data.pv !== undefined)
        pivotVal = arr[data.pv];

    // Build each bar
    for (let i = 0; i < arr.length; i++) {
        const v = arr[i];
        const height = Math.floor(v * heightFactor * 100);

        let color = null;

        if (data.partitioning) {
            if (i >= data.i0 && i < data.i1) {
                // within range
                color = (pivotVal < arr[i]) ? GREATER_ELEMENT_COLOR : LESSER_ELEMENT_COLOR;
            } else if (i === data.pv) {
                color = PIVOT_ELEMENT_COLOR;
            }
        }

        if (!color) color = DEFAULT_ELEMENT_COLOR;

        // Highlight on swap
        if (i === data.s0 || i === data.s1) {
            if (data.swapping) {
                color = SWAPPING_ELEMENT_COLOR;
            } else {
                color = color.lerp(HIGHLIGHT_COLOR, HIGHLIGHT_STRENGTH);
            }
        }

        html += `
        <div style="
            width:${widthPerBar}px;
            height:${height}%;
            background-color:${color.toHex()};
            border-radius:${borderRadius}px;">
        </div>`;
    }

    html += `</div>`;
    return html;
}

let graphElement = document.getElementById("graph");
function buildGraph() {
    const data = getData();
    graphElement = graphElement || assert(document.getElementById("graph"), `Graph container element not found; are you using "graph" as the element ID?`);
    graphElement.innerHTML = getHtmlSrc(data);
}



function onDataHolderFound(dataHolderElement) {
    // Expect that dataHolderElement is now valid; possibly redundant lol
    assert(dataHolderElement, "Data holder element not found but onDataHolderFound was called?");
    
    new MutationObserver((mutations, self) => {
        buildGraph();
    }).observe(dataHolderElement, { characterData: true, childList: true, subtree: true });

    // Initial build
    buildGraph();
    
}

let dataHolderElement = document.getElementById("graph-data"); // won't exist at first load, but this line makes it clear what we're looking for
if (dataHolderElement) {
    onDataHolderFound(dataHolderElement);
} else {
    const dataHolderFinder = new MutationObserver((mutations, self) => {
        for (const mutation of mutations) {
            for (const node of mutation.addedNodes) {
                if (node instanceof HTMLElement && node.id === "graph-data") {
                    onDataHolderFound(node);
                    self.disconnect();
                    return;
                }
            }
        }
    });

    dataHolderFinder.observe(document.documentElement || document, { childList: true, subtree: true });
}