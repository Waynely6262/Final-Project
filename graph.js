class LinkedListNode {
    constructor(thing) {
        this.content = thing;
        this.next = null;
    }
    
    link(node) {
        this.next = node;
    }
}

class Queue {
    constructor() {
        this.head = null;
        this.tail = null;
        this.length = 0;
    }

    add(thing) {
        
        const newNode = new LinkedListNode(thing);
        // adds an element to the tail
        if (this.tail) {
            this.tail.link(newNode);
        } else {
            this.head = newNode;
        }
        this.tail = newNode;
        this.length += 1;
    }

    remove() {

        // removes the head, setting the linked element as the new head
        if (this.length == 0) {
            console.log("Attempted to remove from empty queue");
            return null;
        }
        this.length -= 1;
        const unlinked = this.head;

        this.head = this.head.next;

        if (this.head == null) {
            this.tail = null
        }
        return unlinked.content;
    }

    clear() {
        this.head = null;
        this.tail = null;
        this.length = 0;
    }
}


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

const MINIMUM_ANIMATION_DT = 0.03

const SWAPPING_ELEMENT_COLOR = new Color(80, 255, 80);
const GREATER_ELEMENT_COLOR = new Color(255, 80, 80);
const LESSER_ELEMENT_COLOR = new Color(80, 80, 255);
const HIGHLIGHT_COLOR = new Color(255, 255, 255);
const DEFAULT_ELEMENT_COLOR = Color.fromHex("#c4c8db");
const PIVOT_ELEMENT_COLOR = new Color(255,255,80);
const HIGHLIGHT_STRENGTH = 0.4;

const MAX_BORDER_RADIUS = 16;
const TOTAL_HEIGHT_PX = 200;
const TOTAL_WIDTH_PX = 2000;
const SWAP_ANIMATION_Y_OFFSET = 0.25

let bar_width_memo = {};     // same semantics as Python

function assert(condition, message) { // functions like the lua 'assert' function
    if (!condition) {
        console.error(message || "Assertion failed! (No message provided)");
        throw new Error(message || "Assertion failed! (No message provided)");
    }
    return condition;
}

function easeInOutQuad(t) {
    return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
}

function easeInOutExpo(x) {
    return x === 0
    ? 0
    : x === 1
    ? 1
    : x < 0.5 ? Math.pow(2, 20 * x - 10) / 2
    : (2 - Math.pow(2, -20 * x + 10)) / 2;
}

function wave(x) {
    return Math.sin(x * Math.PI)
}

const DEFAULT_EASE = easeInOutQuad;

// Tweens from one number to another, with a handler and an optional onComplete callback for chaining
function TweenNumber(start, end, duration, ease, onUpdate, onComplete) {
    ease = ease || DEFAULT_EASE;
    duration = duration || 500;
    
    const startTime = performance.now();
    
    function onRenderStep() {
        const currentTime = performance.now();
        const dt = currentTime - startTime;
        const alpha = Math.min(dt / duration, 1);
        const eased = ease(alpha);
        const currentValue = start + (end - start) * eased;
        onUpdate(currentValue);
        if (alpha >= 1) {
            if (onComplete) onComplete();
        } else {
            requestAnimationFrame(onRenderStep);
        }
    }
    
    requestAnimationFrame(onRenderStep);
}


function waitForElementById(id, onFound, timeout) {
    timeout = timeout || 5000;

    const now = performance.now();

    console.log(`Waiting for element with ID: ${id}`);

    function checkElement() {
        let element = document.getElementById(id);
        if (element) {
            onFound(element);
        } else {
            if (performance.now() - now > timeout) {
                console.warn(`Timeout waiting for element with ID: ${id}`);
                return;
            }
            requestAnimationFrame(checkElement);
        }
    }

    checkElement();
}

// Animates swapping two div elements. Does not handle clean up or cloning
function animateSwapElements(div1, div2, duration, ease, onComplete) {
    
    duration = duration || 500;
    
    const overlayRect = graphOverlay.getBoundingClientRect();
    const rect1 = div1.getBoundingClientRect();
    const rect2 = div2.getBoundingClientRect();

    // Hours wasted trying to figuring this out: 4
    
    // I genuinely don't know why this works but it does..
    const x1 = rect1.left - 2*overlayRect.left;
    // const y1 = rect1.bottom;

    const x2 = rect2.left - 2*overlayRect.left;
    // const y2 = rect2.bottom;
    
    const deltaX = x2 - x1;
    // const deltaY = y2 - y1;
    
    div1.style.position = "absolute";
    div2.style.position = "absolute";

    div1.style.left = x1 + "px";
    div1.style.bottom = "0";
    // div1.style.bottom = y1 + "px";
    
    div2.style.left = x2 + "px";
    div2.style.bottom = "0";
    // div2.style.bottom = y2 + "px";
    
    TweenNumber(0, 1, duration, ease, (t) => {
        let dy = -wave(t) * SWAP_ANIMATION_Y_OFFSET * Math.pow(Math.abs(deltaX), 0.75);
        div1.style.transform = `translate(${deltaX * t}px, ${dy}px)`;
        div2.style.transform = `translate(${-deltaX * t}px, ${-dy}px)`;
    }, onComplete);
}


// Elements that are required, but not necessarily available at script load time

let dataHolderElement; // Group 2 (Main)
let graphElement; // Group 1 (Main)
let barContainer; // Group 1
let graphOverlay; // Group 1


function copyElementToOverlay(original) { // ChatGPT
    assert(graphOverlay, "Graph overlay not ready!");

    // Get bounding box relative to viewport
    const rect = original.getBoundingClientRect();

    // Clone the node
    const clone = original.cloneNode(true);

    // Reset positioning context
    clone.style.position = "absolute";
    clone.style.margin = "0";
    clone.style.left = rect.left + window.scrollX + "px";
    clone.style.bottom = rect.bottom + window.scrollY + "px";
    clone.style.width = rect.width + "px";
    clone.style.height = rect.height + "px";

    // Ensure it displays identically
    const computed = window.getComputedStyle(original);
    clone.style.zIndex = computed.zIndex === "auto" ? 9999 : computed.zIndex;

    // Append to body
    graphOverlay.appendChild(clone);

    return clone;
}

// Functions that require the above elements
function updateBars(data) {
    assert(barContainer, "Bar container not ready!");
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
    
    // Update dynamic properties of the container div
    barContainer.style.gap = `${borderRadius}px`;
    
    // Compute height scaling
    let maxVal = Math.max(Math.max(...arr, 4), 4);
    let heightFactor = 1 / maxVal;
    
    let pivotVal = null;
    if (data.pv !== null && data.pv !== undefined)
        pivotVal = arr[data.pv];

    // Build/update bars
    for (let i = 0; i < arr.length; i++) {
        const v = arr[i];
        const height = Math.floor(v * heightFactor * 100);
        
        let color = null;
        
        if (data.partitioning) {
            if (i === data.pv) {
                color = PIVOT_ELEMENT_COLOR;
            } else if (i >= data.i0 && i < data.i1) {
                // within range
                color = (pivotVal < arr[i]) ? GREATER_ELEMENT_COLOR : LESSER_ELEMENT_COLOR;
            }
        }

        if (!color) color = DEFAULT_ELEMENT_COLOR;
        
        // Highlight on swap
        if (i === data.s0 || i === data.s1) {
            if (data.swapping) {
                if (!data.animate_swaps) { // Only change the colour if the swap isn't animated
                    color = SWAPPING_ELEMENT_COLOR;
                }
            } else {
                color = color.lerp(HIGHLIGHT_COLOR, HIGHLIGHT_STRENGTH);
            }
        }

        let barElement = barContainer.children[i]
        
        if (!barElement) {
            barElement = document.createElement("div");
            barContainer.appendChild(barElement); // appending works because the for loop starts from index 0, so previous iterations validate that there are at least (i - 1) children        }
        }
        barElement.style.width = `${widthPerBar}px`;
        barElement.style.height = `${height}%`;
        barElement.style.backgroundColor = color.toHex();
        barElement.style.borderRadius = `${borderRadius}px`;
    }
    
    // Remove excess bars. Another solution is to just hide extra bars
    while (barContainer.children.length > arr.length) {
        barContainer.removeChild(barContainer.lastChild);
    }
}

function swapDom(a, b) {
    const aNext = a.nextSibling;
    const bNext = b.nextSibling;
    const parent = a.parentNode;

    parent.insertBefore(a, bNext);
    parent.insertBefore(b, aNext);
}

function animateSwap(index1, index2, duration) {
    if (duration < MINIMUM_ANIMATION_DT) { swapDom(originalBar1, originalBar2); return; } // for optimization, so we don't create and remove elements before a frame even renders
    assert(graphElement, "Graph element not ready!");
    assert(barContainer, "Bar container not ready!");
    assert(graphOverlay, "Graph overlay not ready!");
    duration = duration || 500;
    
    const bars = barContainer.children;

    // Get the "source" bars
    const originalBar1 = assert(bars[index1], `Bar at i0 ${index1} not found`);
    const originalBar2 = assert(bars[index2], `Bar at i1 ${index2} not found`);

    // Copy and parent to graphOverlay element
    const bar1 = copyElementToOverlay(originalBar1);
    const bar2 = copyElementToOverlay(originalBar2);

    // The original bars may be hidden because they're part of an on-going animation. To avoid this, make sure the cloned bars are visible
    bar1.style.visibility = "visible";
    bar2.style.visibility = "visible";
    // hide original bars
    originalBar1.style.visibility = "hidden";
    originalBar2.style.visibility = "hidden";

    // swap the two actual elements so when their ghosts disappear, this is guaranteed to be updated
    // This is delayed by one frame for the bulk-swap feature, which will read the 'final state' by accident because the dom elements were swapped already
    // requestAnimationFrame(() => {
        swapDom(originalBar1, originalBar2);
    // });

    // Keep track of how many animations are being run on this bar; only the final animation's onComplete callback should set visibility=true,
    // otherwise the element will be visible again too early
    originalBar1.dataset.animationCount = Number(originalBar1.dataset.animationCount || 0) + 1;
    originalBar2.dataset.animationCount = Number(originalBar2.dataset.animationCount || 0) + 1;
    
    
    // run animation
    animateSwapElements(bar1, bar2, duration, easeInOutExpo, () => {
        
        // Delay by one frame because the util function TweenNumber will immediately call onComplete, skipping the rendering for the final frame update
        requestAnimationFrame(() => {
            bar1.remove();
            bar2.remove();
            
            // show original bars, only if this animation is the only active animator of the bar
            // JS auto-interprets strings to numbers when performing arithmetic operations
            originalBar1.dataset.animationCount = Number(originalBar1.dataset.animationCount || 0) - 1;
            originalBar2.dataset.animationCount = Number(originalBar2.dataset.animationCount || 0) - 1;

            // As long as math is mathing, the animationCount at this point should never be below 0
            if (originalBar1.dataset.animationCount === "0") originalBar1.style.visibility = "visible";
            if (originalBar2.dataset.animationCount === "0") originalBar2.style.visibility = "visible";
        });    
    });
    
}


function update(data) {
    
    assert(graphElement, `Graph container element not found; are you using "graph" as the element ID?`);
    // update bar appearance
    updateBars(data);
    
    
    if (data.animate_swaps) {
        // handle focused swap
        if (data.swapping) animateSwap(data.s0, data.s1, data.dt * 1000);
        
        // handle bulk swaps
        
        if (data.bulk_swap) {
            for (let i = 0; i < data.bulk_swap.length; i++) {
                animateSwap(data.bulk_swap[i][0], data.bulk_swap[i][1], data.dt * 1000);
            }
        }
    }
}

let framesWaiting = new Queue();

// Limits data to be processed per-frame, so nothing is skipped
function onNewData() {

    assert(dataHolderElement, "Data holder element not ready!");
    // dataElement is expected to be a <script> with JSON content in its innerHTML

    const data = JSON.parse(dataHolderElement.innerHTML);
    
    framesWaiting.add(data);
    if (framesWaiting.length > 1) {
        if (!data.do_queue) {
            framesWaiting.clear(); // empty the queue
            framesWaiting.add(data); // add the only element waiting
        }
        return;
    }

    function onFrame() {
        update(framesWaiting.remove())
        if (framesWaiting.length > 0) {
            requestAnimationFrame(onFrame)
        }
    }
    requestAnimationFrame(onFrame)
}

// Main


// Group 1; Will initialize graphElement, barContainer, graphOverlay
waitForElementById("graph", (ele) => {
    console.log("Graph element found!");
    graphElement = ele;
    
    barContainer = document.createElement("div");
    barContainer.style.display = "flex";
    barContainer.style.justifyContent = "center";
    barContainer.style.alignItems = "flex-end";
    barContainer.style.height = `${TOTAL_HEIGHT_PX}px`;
    graphElement.appendChild(barContainer);
    
    
    graphOverlay = document.createElement("div");
    graphOverlay.style.position = "relative";
    graphOverlay.style.top = "0";
    graphOverlay.style.left = "0";
    graphOverlay.style.width = "100%";
    graphOverlay.style.height = "100%";
    graphOverlay.style.pointerEvents = "none";
    graphOverlay.style.transparent = "true";

    graphOverlay.style.display = "block";
    graphOverlay.style.margin = "0";
    graphOverlay.style.padding = "0";
    graphOverlay.style.textAlign = "left";
    
    graphOverlay.id = "graph-overlay";
    graphElement.appendChild(graphOverlay);
    
    
});
    
// Group 2;Will initialize dataHolderElement
waitForElementById("graph-data", (ele) => {
    console.log("Data holder element found!");
    dataHolderElement = ele;

    new MutationObserver((mutations, self) => {
        onNewData();
    }).observe(dataHolderElement, { characterData: true, childList: true, subtree: true });
    // Initial build
    onNewData();
});
