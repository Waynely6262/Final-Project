from math import floor
from deprecated import deprecated
import random as rand
from asyncio import sleep as wait

# UTILS
def lerp(v0: float, v1: float, a: float) -> float: # o(1) 
    return (1 - a) * v0 + (v1 * a)

def is_sorted(arr: list[int]): # o(n) time
    for i in range(1, len(arr)):
        if arr[i - 1] > arr[i]:
            return False
    return True

def regenerate(arr, elements: int | None = 50): # o(n) time
    if elements == None: elements = 50
    arr.clear()
    for i in range(elements):
        arr.append(rand.randint(1,1000))
    return arr

# Fisher-Yates shuffle, with a shuffle_strength variable representing the percentage likelihood that an element will be swapped
def shuffle(arr, shuffle_strength: float=1.0): # o(n) time worst case
    for i in range(len(arr) - 1, 0, -1):
        if rand.random() > shuffle_strength: continue
        j = rand.randint(0, i)
        arr[i], arr[j] = arr[j], arr[i]
    return arr
# END OF UTILS


# UTILITY CLASSES
class Job:
    def __init__(self, start, end):
        self.i0 = start
        self.i1 = end
    def get_pivot_index(self, alpha: float=1) -> int:
        return floor(lerp(self.i0, self.i1, alpha))


# Color class
BASE_16 = ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']
class Color:
    r: int
    g: int
    b: int

    def __init__(self, r: str | int, g: int, b: int):
        self.r = r
        self.g = g
        self.b = b

    @classmethod
    def from_hex(_, src: str):
        src = src.lstrip("#")
        
        r = int(src[0:2], 16)
        g = int(src[2:4], 16)
        b = int(src[4:6], 16)
        return Color(r, g, b)

    def _to_hex(self, n: int) -> str:
        # Convert 0–255 to a 2-digit hex string.
        high = n // 16
        low = n % 16
        return BASE_16[high] + BASE_16[low]

    def get_hex(self) -> str:
        # Return a hex-code in the form of #ffffff
        return f"#{self._to_hex(self.r)}{self._to_hex(self.g)}{self._to_hex(self.b)}"

    def lerp(self, other: "Color", alpha: float) -> "Color":
        #,Return a new color interpolated between self and other
        r = int(lerp(self.r, other.r, alpha))
        g = int(lerp(self.g, other.g, alpha))
        b = int(lerp(self.b, other.b, alpha))
        return Color(r, g, b)
# END OF UTILITY CLASSES


# CONFIG
SWAPPING_ELEMENT_COLOR = Color(80,255,80)
GREATER_ELEMENT_COLOR = Color(255,80,80)
LESSER_ELEMENT_COLOR = Color(80,80,255)
HIGHLIGHT_COLOR = Color(255,255,255)
DEFAULT_ELEMENT_COLOR = Color.from_hex("#c4c8db") # grey
PIVOT_ELEMENT_COLOR = Color(255,160,80)
HIGHLIGHT_STRENGTH = 0.75
MAX_BORDER_RADIUS = 16
# Chart Size
TOTAL_HEIGHT_PX = 200
TOTAL_WIDTH_PX = 2000
# END OF CONFIG

# CLASSES
MAX_ELEMENTS = TOTAL_WIDTH_PX
bar_width_memo = {} # this can be used across all instances of the class, because they will all return the same value 

class VisualState:
    arr: list[int]
    partitioning: bool = False
    i0: int = 0 # Lower interval index
    i1: int = 0 # Upper interval index
    pv: int | None = None # Pivot index
    s0: int | None = None # First swap index
    s1: int | None = None # Second swap index
    swapping: bool = False # Whether a swap is occurring. The swap indexes will be coloured differently if (swapping)
    def __init__(self):
        self.arr = regenerate([])

    def get_html_src(self) -> str:

        length = len(self.arr)


        border_radius = MAX_BORDER_RADIUS # Maximum radius, which may be internally be reduced to accomodate for fitting large numbers of elements
        # Reduce the border radius if width_per_bar is too little. This is an o(log(n)) operation. width_per_bar is initialized a either the memoized result, or something that meets the while condition, since there is no do-while in python. The memoized result already met the inverse condition previously, so it is assumed to never enter the while loop. 
        width_per_bar = bar_width_memo.get(str(length)) or border_radius * 2
        # Calculated by distributing the total allocated width (TOTAL_WIDTH_PX) while accounting for the border radius. Then, the maximum between the calculated distribution and 1 is used.
        while width_per_bar <= border_radius * 2:
            border_radius //= 2
            width_per_bar = max(( TOTAL_WIDTH_PX - (border_radius * (length + 2)) ) // max(length, 1), 1)

        # Avoid repeatedly calculating the bar width by memoizing results
        bar_width_memo[str(length)] = width_per_bar

        # Main div
        source = f'<div style="display:flex;justify-content:center;align-items:flex-end;height:{TOTAL_HEIGHT_PX}px;gap:{border_radius}px;">'

        # Get maximum value from array, but require it to be at least 4 to avoid division by zero. Get the inverse of that value and use it as the multiplier for determining the percentage of the maximum height of each bar
        max_v = len(self.arr) and max(max(self.arr), 4) or 4

        height_factor = 1 / max_v # Do this to optimize division; think of it as how much the pixel height increases per 1 value.

        if self.pv != None:
            pivot_val = self.arr[self.pv]
            
        for i, v in enumerate(self.arr):
            height = int((v * height_factor) * 100)

            # Color any specified bars differently

            color: Color = None
            if self.partitioning:
                if i < self.i1 and i >= self.i0:
                    # Within the partition's range
                    # Elements larger than the pivot and smaller than the pivot are different colored, representing where they should end up
                    color = pivot_val < self.arr[i] and GREATER_ELEMENT_COLOR or LESSER_ELEMENT_COLOR

                # We don't have to make sure 'pv' isn't 'None' because comparing int and None is a supported operation
                elif i == self.pv:
                    # Is the pivot element
                    color = PIVOT_ELEMENT_COLOR
            # Anything else
            color = color or DEFAULT_ELEMENT_COLOR

            # Highlight active_indices
            if i == self.s0 or i == self.s1:
                # At this point, color is already guaranteed to be defined
                color = self.swapping and SWAPPING_ELEMENT_COLOR or color.lerp(HIGHLIGHT_COLOR, HIGHLIGHT_STRENGTH)
            # html source for each individual bar
            source += f'''
            <div style="
                width: {width_per_bar}px;
                height: {height}%;
                background-color:{color.get_hex()};
                border-radius:{border_radius}px;">
            </div>
            '''

        source += '</div>'
        return source
# bounded by 32-bit int lim.
START_CALL_ID = -2**31
MAX_CALL_ID = 2**31 - 1
class InternalState:

    is_active: bool = False # Whether sorting is active
    step_sort_jobs: list[Job] | None = None
    call_id: int = START_CALL_ID
    pv_alpha: float = 1.0



    # Functions used to ensure that only one thing is running at once.
    def new_lock(self):
        this_id = self.call_id + 1
        # Ensure continuity, if the user hits the max call ids, set it back to -2**31
        if this_id > MAX_CALL_ID:
            this_id = START_CALL_ID

        self.is_active = True
        self.call_id = this_id
        return this_id

    def lock_active(self):
        return self.is_active
    
    def is_lock_owner(self, caller_id) -> bool:
        return self.call_id == caller_id

    def close_lock(self, id):
        # Only the lock owner can close the active lock
        if self.call_id == id:
            self.is_active = False
    
# END OF CLASSES



# QUICK SORT
def partition(chart_info: VisualState, start: int, end: int, alpha: float=1):
    get_pivot_index = floor(lerp(start, end, alpha))
    
    
    arr = chart_info.arr
    # Visualize moving the pivot from its original location to the end of the sub-array

    # Update graphics (intent)

    chart_info.pv = get_pivot_index
    chart_info.s0 = get_pivot_index
    chart_info.s1 = end
    chart_info.swapping = True
    
    yield
    
    arr[get_pivot_index], arr[end] = arr[end], arr[get_pivot_index]

    # Update graphics (result)
    chart_info.pv = end
    yield

    free_index = start
    pivot_index = end

    pivot_value = arr[pivot_index]

    for i in range(start, end):
        
        # check if this element is smaller than the pivot. If it is, then an index is taken up (so free_index should be incremented).
        do_swap = arr[i] <= pivot_value
        swap_is_redunant = i == free_index

        # Update graphics (intent) before swapping
        chart_info.s0 = i
        chart_info.s1 = free_index
        chart_info.swapping = do_swap and not swap_is_redunant
        yield
        
        if do_swap:

            # Skip update and variable assignment if the location and destination are the same
            if not swap_is_redunant:
                # Move the small element to the free index, then fill the gap with the other arbitrary element
                arr[free_index], arr[i] = arr[i], arr[free_index]

                # Update graphics (result) after the swap
                chart_info.swapping = False
                yield
            
            # Increment the variable for the next free index
            free_index += 1
        

    # Update graphics (result) before the swap
    chart_info.s0 = pivot_index
    chart_info.s1 = free_index
    chart_info.swapping = True
    yield


    # Move the pivot element to the free index that was found, swapping with the current element in the free index
    arr[pivot_index], arr[free_index] = arr[free_index], pivot_value
    
    # Update graphics (result) after the swap
    chart_info.swapping = False
    yield

    # Return the free index, which has the position of the semi-sorted element, the pivot
    return free_index

# Recursive quick-sort, only left here for the concept. May not be up-to-date with the latest features
@deprecated
def quick_sort(arr: list[int], start: int = 0, end: int | None = None) -> list[int]:
    # Dynamic default value for the end-point
    end = end == None and len(arr) - 1 or end
    
    # Base case: The sub-array has reached length <= 1
    if start >= end:
        return
    
    partitioner = partition(arr, start, end)

    try:
        while True:
            next(partitioner)
    except StopIteration as result:
        # Get the pivot point's index
        pivot_index = result.value

    # Sort items below the pivot point's index

    quick_sort(arr, start, pivot_index - 1)
    # Sort items above the pivot point's index
    quick_sort(arr, pivot_index + 1, end)

    return arr

def quick_sort_iterative(chart_info: VisualState, session_info: InternalState, step_sort: bool=False, iterations_allowed: int | None = 1, use_random_pivot: bool=False):

    arr = chart_info.arr

    # Avoid edge-case for len(arr) - 1
    if len(arr) <= 1:
        session_info.step_sort_jobs = []
        return chart_info, session_info
    # If jobs doesn't exist or jobs is empty, create default 'jobs' value which considers the entire array

    jobs = session_info.step_sort_jobs and session_info.step_sort_jobs or [Job(0, len(arr) - 1)]
    if step_sort:
        session_info.step_sort_jobs = jobs
    # Resync, in case jobs created a new array

    # Used to support the limited iteration count feature
    iterations_finished = 0
    # Keep iterating while there are jobs and the number of maximum iterations on this function call has not been reached
    while jobs and (not step_sort or iterations_finished < iterations_allowed):
        
        current_job = jobs.pop()
        # Small shortcut by removing indexing on the current_job object
        i0 = current_job.i0
        i1 = current_job.i1
        chart_info.i0 = i0
        chart_info.i1 = i1
        chart_info.partitioning = True


        partitioner = partition(chart_info, i0, i1, use_random_pivot and rand.random() or session_info.pv_alpha)

        # Conventional structure for python generators (I think?)
        try:
            while True:
                next(partitioner)
                yield
        except StopIteration as result:
            # Get the pivot point's index
            pivot_index = result.value


            
        # Only add the job if the start is smaller than the end
        if i0 < pivot_index - 1:
            # Left side of the pivot
            jobs.append(Job(i0, pivot_index - 1))
        if pivot_index + 1 < i1:
            # Right side of the pivot
            jobs.append(Job(pivot_index + 1, i1))

        iterations_finished += 1
    chart_info.partitioning = False

# Main
import gradio as gr

with gr.Blocks() as demo:


    # INITIALIZE ELEMENTS

    # chart_info_state stores components relevant to updating the html bar chart.
    # This gr.State object is specified as "part of an event listener's output" whenever the event handler will update the chart info state.
    chart_info_state = gr.State(VisualState())
    
    # session_info_state stores components that are irrelevant to graphics: Essentially, values that are only used internally (in the back-end)
    # An assumption is made that type(gr.State()) objects pass their 'value' attribute whenever the gr.State object is used as input, meaning that references are maintained and session_info never needs to be used as output.
    session_info_state = gr.State(InternalState())

    gr.Markdown("# Quicksort: by Wayne")
    
    html_chart = gr.HTML(chart_info_state.value.get_html_src())

    iteration_interval_slider = gr.Slider(label="Iteration Interval (seconds)", minimum=0, maximum=2, value=0.05)
    iterations_per_step_slider = gr.Slider(label="Iterations per Step", minimum=1, maximum=10, value=1, step=1)
    element_count_slider = gr.Slider(label="Total Elements", minimum=1, maximum=MAX_ELEMENTS, value=50, step=1)
    shuffle_strength_field = gr.Slider(label= "Shuffle Strength", minimum=0.0, maximum=1.0, value=0.1)

    show_swaps_option = gr.Checkbox(label="Show Swaps", value=True)

    pv_alpha_use_random_checkbox = gr.Checkbox(label="Use Random Pivot", value=False)
    pv_alpha_slider = gr.Slider(label="Custom Pivot Point", minimum=0, maximum=1, value=1)

    shuffle_button = gr.Button("Shuffle Elements")
    stop_button = gr.Button("Stop Sorting (May not respond immediately for large arrays)")
    reset_button = gr.Button("Regenerate Elements")
    step_button = gr.Button("Step Sort")
    sort_button = gr.Button("Complete Sort")

        

    # END OF INITIALIZE ELEMENTS

    # EVENT LISTENERS & HANDLERS
    # The following code is meant to follow the structure of Event Handler -> Event Listener, which allows easy correspondence, especially for receiving input and interfacing output to the proper gradio components.

    # Step-sort
    async def step_button_on_click(
        chart_info: VisualState,
        session_info: InternalState,
        wait_interval: float,
        steps_src: float, # This has been made to be received as an int, but I'm leaving the parsing as a redundancy.
        show_swaps: bool,
        use_random_pivot: bool
    ):
        print("step_button on click")

        # Update the global call id, and is_active state
        this_id = session_info.new_lock()

        quick_sort_generator = quick_sort_iterative(chart_info, session_info, step_sort=True, iterations_allowed = round(steps_src), use_random_pivot=use_random_pivot)
        
        try:
            while session_info.is_lock_owner(this_id):
                # Under the assumption that chart_info's reference is maintained, we don't need any return values! However, it could still be worth noting where modifications are inexplicitly made.
                next(quick_sort_generator) # modifies chart_info
                if show_swaps:
                    yield chart_info.get_html_src()
                    await wait(wait_interval)
        except StopIteration as result:
            if not show_swaps:
                chart_info.partitioning = True
                yield chart_info.get_html_src()
                chart_info.partitioning = False
                await wait(wait_interval)
        
        # If this thread doesn't hold the latest call_id, exit to avoid interrupting a different UI update
        session_info.close_lock(this_id)

    step_button.click(
        step_button_on_click, 
        [# 6
            chart_info_state,
            session_info_state,
            iteration_interval_slider,
            iterations_per_step_slider,
            show_swaps_option,
            pv_alpha_use_random_checkbox,
        ], 
        [
            html_chart,
        ], queue=True, concurrency_limit=None
    )

    async def sort_button_on_click(chart_info: VisualState, session_info: InternalState, wait_interval: float, show_swaps: bool, use_random_pivot: bool):

        # If pivot_alpha isn't 1, the sort function will unsort the array. This if statement will prevent that from happening
        if is_sorted(chart_info.arr):
            gr.Info("The array is fully sorted.")
            return

        this_id = session_info.new_lock()

        local_jobs = []
        iteration_one = True
        while session_info.is_lock_owner(this_id) and (local_jobs or iteration_one):
            iteration_one = False

            quick_sort_generator = quick_sort_iterative(chart_info, session_info, use_random_pivot=use_random_pivot)

            try:
                while session_info.is_lock_owner(this_id):
                    next(quick_sort_generator) # modifies chart_info
                    if show_swaps:
                        yield chart_info.get_html_src()
                        await wait(wait_interval) 
            except StopIteration as result:
                local_jobs = result.value
                # Only do this  if not showing swaps. Since the full-sort feature relies on creating a quick_sort_iterative generator with argument iterations_allowed=1, this function will call wait() too many times, reducing the animation speed.
                if not show_swaps:
                    chart_info.partitioning = True
                    yield chart_info.get_html_src()
                    chart_info.partitioning = False
                    await wait(wait_interval)

        session_info.close_lock(this_id)

        yield chart_info.get_html_src()

    sort_button.click(sort_button_on_click, [
        chart_info_state,
        session_info_state,
        iteration_interval_slider, # How long to wait between each update
        show_swaps_option, # Whether to show swaps being performed, or to just show partitions
        pv_alpha_use_random_checkbox, # Whether to randomize the pivot alpha
    ], [html_chart], queue=True, concurrency_limit=None)

    def stop_button_on_click(session_info: InternalState):
        # Overwrites other locks, then closes itself; result: peace and quiet (nothing will be running)
        session_info.close_lock(session_info.new_lock())

    stop_button.click(stop_button_on_click, [session_info_state], [])

    def reset_button_on_click(chart_info: VisualState, session_info: InternalState, element_count_src: float):
        if session_info.lock_active():
            gr.Info("Sorting is in progress, can't refresh")
            return None
        # Clear step-sort pending jobs
        session_info.step_sort_jobs = None

        # Regenerate randomized elements for the array
        regenerate(chart_info.arr, floor(element_count_src))

        # Update states
        return chart_info.get_html_src()
    reset_button.click(reset_button_on_click, [chart_info_state, session_info_state, element_count_slider], [html_chart])

    # Since this doesn't affect the number of elements in the list, it won't cause the program to fail. I will let this be callable mid-sort, just for fun
    def shuffle_button_on_click(chart_info: VisualState, shuffle_strength: float):
        shuffle(chart_info.arr, shuffle_strength)
        return chart_info.get_html_src()
    shuffle_button.click(shuffle_button_on_click, [chart_info_state, shuffle_strength_field], [html_chart])

    def pv_alpha_slider_on_change(session_info: InternalState, alpha):
        # Updates a variable so the pivot alpha can be adjusted during an on-going sort
        session_info.pv_alpha = alpha
    pv_alpha_slider.change(pv_alpha_slider_on_change, [session_info_state, pv_alpha_slider])



demo.launch(share=True)