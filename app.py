from math import floor, log
from deprecated import deprecated
import random as rand
from asyncio import sleep as wait
import json

# UTILS
def lerp(v0: float, v1: float, a: float) -> float: # o(1) 
    return (1 - a) * v0 + (v1 * a)

def is_sorted(arr: list[int]): # o(n) time
    for i in range(1, len(arr)):
        if arr[i - 1] > arr[i]:
            return False
    return True

def regenerate(arr: list[int], elements: int | None = 50): # o(n) time
    if elements == None: elements = 50
    arr.clear()
    for _ in range(elements):
        arr.append(rand.randint(1,1000))
    return arr

# Fisher-Yates shuffle, with a shuffle_strength variable representing the percentage likelihood that an element will be swapped
def shuffle(arr: list[int], shuffle_strength: float=1.0): # o(n) time worst case
    for i in range(len(arr) - 1, 0, -1):
        if rand.random() > shuffle_strength: continue
        j = rand.randint(0, i)
        arr[i], arr[j] = arr[j], arr[i]
    return arr
# END OF UTILS


# UTILITY CLASSES
class Job:
    def __init__(self, start: int, end: int):
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

    def __init__(self, r: int, g: int, b: int):
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

# Make sure these matches the identifiers used in graph.js

HTML_DATA_HOLDER_ELEMENT_ID = "graph-data" # HTML element ID where the graph data JSON is stored
HTML_GRAPH_ELEMENT_ID = "graph" # HTML element ID where the graph will be rendered

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
    dt: float = 0 # Expected time delay before proceeding
    swapping: bool = False # Whether a swap is occurring. The swap indexes will be coloured differently if (swapping)
    animate_swaps: bool = True # Whether to animate swaps
    
    def __init__(self):
        self.arr = regenerate([])
        self.animate_swaps = True # Make sure __dict__ knows this value exists? Idk if this is necessary

    def reset_visuals(self):
        self.i0 = 0
        self.i1 = len(self.arr) - 1
        self.swapping = False
        self.s0 = None
        self.s1 = None
        self.pv = None
        self.dt = 0

    def get_wait_multiplier_for_current_state(self) -> float:
        if not self.animate_swaps: return 1 # The purpose of the delay was just to make sure the animation doesn't happen too quickly if elements are further apart. If animatiosn aren't happening, just use a multiplier of 1
        if not (self.s0 and self.s1): return 1
        return log(2 + abs(self.s0 - self.s1), 2)
    
    def to_embedded_json(self) -> str:
        json_src = json.dumps(self.__dict__)
        return f"<script id=\"{HTML_DATA_HOLDER_ELEMENT_ID}\" type=\"application/json\">{json_src}</script>"
    
# bounded by 32-bit int lim.
START_CALL_ID = -2**31
MAX_CALL_ID = 2**31 - 1
class InternalState:

    is_active: bool = False # Whether sorting is active
    step_sort_jobs: list[Job] | None = None
    call_id: int = START_CALL_ID
    pv_alpha: float = 1.0

    wait_interval: float = 0.25

    use_random_pv: bool = False
    show_queries: bool = True
    show_comparisons: bool = True

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
    
    def is_lock_owner(self, caller_id: int) -> bool:
        return self.call_id == caller_id

    def close_lock(self, id: int):
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

def quick_sort_iterative(chart_info: VisualState, session_info: InternalState, step_sort: bool=False, iterations_allowed: int = 1):

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


        partitioner = partition(chart_info, i0, i1, session_info.use_random_pv and rand.random() or session_info.pv_alpha)

        # Conventional structure for python generators (I think?)
        try:
            while True:
                next(partitioner)
                yield
        except StopIteration as result:
            # Get the pivot point's index
            pivot_index = result.value
            yield True # Indicate that a job has finished


            
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

with open("graph.js", "r") as js_file:
   graph_builder_src_js = js_file.read()


with gr.Blocks() as demo:


    # INITIALIZE ELEMENTS

    # chart_info_state stores components relevant to updating the html bar chart.
    # This gr.State object is specified as "part of an event listener's output" whenever the event handler will update the chart info state.
    chart_info_state = gr.State(value=VisualState())
    
    # session_info_state stores components that are irrelevant to graphics: Essentially, values that are only used internally (in the back-end)
    # An assumption is made that type(gr.State()) objects pass their 'value' attribute whenever the gr.State object is used as input, meaning that references are maintained and session_info never needs to be used as output.
    session_info_state = gr.State(value=InternalState()) # luau typecheck: gr.State & {value: InternalState}

    gr.Markdown("# Quicksort: by Wayne")
    
    hidden_graph_data = gr.HTML(value=chart_info_state.value.to_embedded_json())

    html_chart = gr.HTML(value=f"<div></div>", elem_id=HTML_GRAPH_ELEMENT_ID)


    # Visual update controls
    with gr.Row():
        show_queries_option = gr.Checkbox(label="Show Queries", value=session_info_state.value.show_queries) # Uses session info because py prompts visual updates, so js doesnt need this
        show_comparisons_option = gr.Checkbox(label="Show Comparisons", value=session_info_state.value.show_comparisons) # Uses session info because py prompts visual updates, so js doesnt need this
        animate_swaps_option = gr.Checkbox(label="Animate Swaps", value=chart_info_state.value.animate_swaps) # Uses chart info because js needs to know whether to animate

    # Pivot controls
    with gr.Row():
        use_random_pv_option = gr.Checkbox(label="Use Random Pivot", value=session_info_state.value.use_random_pv)
        pv_alpha_slider = gr.Slider(label="Custom Pivot Point", minimum=0, maximum=1, value=1)

    # Unsorting controls
    with gr.Row():
        with gr.Column():
            element_count_slider = gr.Slider(label="Total Elements", minimum=1, maximum=MAX_ELEMENTS, value=50, step=1)
            reset_button = gr.Button("Regenerate Elements")
        with gr.Column():
            shuffle_strength_field = gr.Slider(label= "Shuffle Strength", minimum=0.0, maximum=1.0, value=0.1)
            shuffle_button = gr.Button("Shuffle Elements")
            

    # Sorting controls
    with gr.Row():
        with gr.Column():
            iterations_per_step_slider = gr.Slider(label="Iterations per Step", minimum=1, maximum=10, value=1, step=1)
            step_button = gr.Button("Step Sort")
        with gr.Column():
            iteration_interval_slider = gr.Slider(label="Iteration Interval (seconds)", minimum=0.001, maximum=2, value=session_info_state.value.wait_interval)
            stop_button = gr.Button("Stop Sorting (May not respond immediately for large arrays)")
            sort_button = gr.Button("Complete Sort")


    with open("README.md", "r") as instructions_file:

        try:
            readme_src = instructions_file.read()
            gr.Markdown(readme_src)
        except Exception as e:
            gr.Markdown("Failed to load README instructions.")


    # END OF INITIALIZE ELEMENTS

    # EVENT LISTENERS & HANDLERS
    # The following code is meant to follow the structure of Event Handler -> Event Listener, which allows easy correspondence, especially for receiving input and interfacing output to the proper gradio components.

    # Step-sort
    async def step_button_on_click(
        chart_info: VisualState,
        session_info: InternalState,
        steps_src: float, # This has been made to be received as an int, but I'm leaving the parsing as a redundancy.
    ):

        # Update the global call id, and is_active state
        this_id = session_info.new_lock()

        quick_sort_generator = quick_sort_iterative(chart_info, session_info, step_sort=True, iterations_allowed = round(steps_src))
        
        try:
            while session_info.is_lock_owner(this_id):
                # job_finished is a bool that stores whether a job was completed on this yield
                job_finished = next(quick_sort_generator)
                if session_info.show_queries:
                    if session_info.show_comparisons or chart_info.swapping:
                        final_wait_interval = session_info.wait_interval * chart_info.get_wait_multiplier_for_current_state()
                        chart_info.dt = final_wait_interval
                        yield chart_info.to_embedded_json()
                        await wait(final_wait_interval)

                elif job_finished:
                    chart_info.partitioning = True
                    yield chart_info.to_embedded_json()
                    chart_info.partitioning = False
                    await wait(session_info.wait_interval)
        except StopIteration:
            pass
        
        # If this thread doesn't hold the latest call_id, exit to avoid interrupting a different UI update
        session_info.close_lock(this_id)

    step_button.click(
        step_button_on_click, 
        [
            chart_info_state,
            session_info_state,
            iterations_per_step_slider,
        ], 
        [
            hidden_graph_data,
        ], queue=True, concurrency_limit=None, 
    )

    async def sort_button_on_click(chart_info: VisualState, session_info: InternalState):

        # If pivot_alpha isn't 1, the sort function will unsort the array. This if statement will prevent that from happening
        if not is_sorted(chart_info.arr):

            this_id = session_info.new_lock()

            quick_sort_generator = quick_sort_iterative(chart_info, session_info)

            try:
                while session_info.is_lock_owner(this_id):
                    # job_finished is a bool
                    job_finished = next(quick_sort_generator)
                    if session_info.show_queries:
                        if session_info.show_comparisons or chart_info.swapping:
                            final_wait_interval = session_info.wait_interval * chart_info.get_wait_multiplier_for_current_state()
                            chart_info.dt = final_wait_interval
                            yield chart_info.to_embedded_json()
                            await wait(final_wait_interval)
                        
                    elif job_finished:
                        chart_info.partitioning = True
                        yield chart_info.to_embedded_json()
                        chart_info.partitioning = False
                        await wait(session_info.wait_interval)

            except StopIteration:
                pass

            session_info.close_lock(this_id)
            
        else:
            gr.Info("The array is fully sorted.")
            pass
        yield chart_info.to_embedded_json() # DO I NEED THIS?? LET'S FIND OUT. (Yes we need this, otherwise chart_info_state will be set to nil because it's listed as an output component and I guess at least one yield/return is required. But we cannot return a value on an async function)

    sort_button.click(sort_button_on_click, [
        chart_info_state,
        session_info_state,
    ], [hidden_graph_data], queue=True, concurrency_limit=None, )

    def stop_button_on_click(session_info: InternalState):
        # Overwrites other locks, then closes itself; result: peace and quiet (nothing will be running)
        session_info.close_lock(session_info.new_lock())

    stop_button.click(stop_button_on_click, [session_info_state], [])

    def reset_button_on_click(chart_info: VisualState, session_info: InternalState, element_count_src: float):
        if session_info.lock_active():
            gr.Info("Sorting is in progress, can't refresh")
            return chart_info.to_embedded_json()
        # Clear step-sort pending jobs
        session_info.step_sort_jobs = None

        # Regenerate randomized elements for the array
        regenerate(chart_info.arr, floor(element_count_src))
        chart_info.reset_visuals()

        # Update states
        return chart_info.to_embedded_json()
    reset_button.click(reset_button_on_click, [chart_info_state, session_info_state, element_count_slider], [hidden_graph_data], )

    # Since this doesn't affect the number of elements in the list, it won't cause the program to fail. I will let this be callable mid-sort, just for fun
    def shuffle_button_on_click(chart_info: VisualState, shuffle_strength: float):
        shuffle(chart_info.arr, shuffle_strength)
        # chart_info.reset_visuals() # This is disabled because it will modify chart_info.pv, which causes issues because the sort algorithm doesn't reset chart_info.pv even if it's currently active
        return chart_info.to_embedded_json()
    shuffle_button.click(shuffle_button_on_click, [chart_info_state, shuffle_strength_field], [hidden_graph_data], )

    def pv_alpha_slider_on_change(session_info: InternalState, alpha: float):
        # Updates a variable so the pivot alpha can be adjusted during an on-going sort
        session_info.pv_alpha = alpha
    pv_alpha_slider.change(pv_alpha_slider_on_change, [session_info_state, pv_alpha_slider])

    def use_random_pv_option_on_change(session_info: InternalState, value: bool):
        session_info.use_random_pv = value
        return gr.update(interactive=not value)
    use_random_pv_option.change(use_random_pv_option_on_change, [session_info_state, use_random_pv_option], [pv_alpha_slider])

    def iteration_interval_slider_on_change(session_info: InternalState, value: float):
        session_info.wait_interval = value
    iteration_interval_slider.change(iteration_interval_slider_on_change, [session_info_state, iteration_interval_slider])

    # option row
    def show_queries_option_on_change(session_info: InternalState, show_queries: bool): # Controls whether swaps and comparisons are shown
        session_info.show_queries = show_queries

        # The sole purpsoe of reading show_comparisons in this event handler is to update the interactability of the animate_swaps option
        return gr.update(interactive=show_queries), gr.update(interactive=show_queries)
    show_queries_option.change(show_queries_option_on_change, [session_info_state, show_queries_option], [show_comparisons_option, animate_swaps_option])

    def show_comparisons_option_on_change(session_info: InternalState, show_comparisons: bool):
        session_info.show_comparisons = show_comparisons
    show_comparisons_option.change(show_comparisons_option_on_change, [session_info_state, show_comparisons_option])

    def animate_swaps_option_on_change(chart_info: VisualState, animate_swaps: bool):
        chart_info.animate_swaps = animate_swaps
    animate_swaps_option.change(animate_swaps_option_on_change, [chart_info_state, animate_swaps_option])

    # end of option row


demo.launch(share=True, head=f"<script defer>{graph_builder_src_js}</script>", 
            
css = """
#warning {background-color: #FFCCCB}
.feedback textarea {font-size: 24px !important}
"""
)