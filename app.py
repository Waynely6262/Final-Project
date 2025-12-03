from typing import Any, AsyncGenerator, Generator
from math import floor, log
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
    
    algorithm: str = "Quick-Sort"

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

def bubble_sort_iterative(chart_info: VisualState, start: int | None=None, end: int | None=None):

    l = len(chart_info.arr)
    fin = l - 1

    chart_info.i1 = fin
    chart_info.partitioning = True

    for query_begin in range(start or 0, min(fin, end or fin)):
        did_swap = False
        chart_info.i0 = query_begin
        for query in range(query_begin, fin - 1):
            plus1 = query + 1

            chart_info.pv = query
            chart_info.s0 = query
            chart_info.s1 = plus1
            if chart_info.arr[query] > chart_info.arr[plus1]:
                did_swap = True
                chart_info.swapping = True
                yield
                chart_info.pv = plus1
                chart_info.arr[query], chart_info.arr[plus1] = chart_info.arr[plus1], chart_info.arr[query]
                chart_info.swapping = False
            yield
        if not did_swap:
            chart_info.partitioning = False
            return

    chart_info.partitioning = False
                
        


# SELECTION SORT
def selection_sort_iterative(chart_info: VisualState, start: int | None=None, end: int | None=None):

    chart_info.partitioning = True

    l = len(chart_info.arr)
    final_index = l - 1

    chart_info.i1 = l

    for i in range(start or 0, min(final_index, end or final_index)):
        chart_info.swapping = False
        chart_info.pv = i
        chart_info.i0 = i
        chart_info.s0 = i

        low_i = i
        low_v = chart_info.arr[i]
        # If the lower bound is greater than the upper bound, the loop just won't run, so we don't have to worry about it
        for q in range(i + 1, final_index - 1):
            chart_info.s1 = q
            if chart_info.arr[q] < low_v:
                low_v = chart_info.arr[q]
                low_i = q
                chart_info.pv = low_i
            yield



        if low_i != i:
            chart_info.s0 = i
            chart_info.s1 = low_i
            chart_info.swapping = True
            yield
            chart_info.arr[i], chart_info.arr[low_i] = chart_info.arr[low_i], chart_info.arr[i]
        chart_info.swapping = False
        yield True
    chart_info.partitioning = False
# END OF SELECTION SORT

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
    chart_info.swapping = False
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
        return
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

# GRADIO HANDLERS

# bubblesort

def step_bubblesort_gen(chart_info: VisualState, session_info: InternalState, steps: int):

    if session_info.step_sort_jobs:
        current_job = session_info.step_sort_jobs.pop()
        i0 = current_job.i0
    else:
        i0 = 0

    generator = bubble_sort_iterative(chart_info, start=i0, end=i0 + steps)
    
    try:
        while True:
            yield next(generator)
            
    except StopIteration:
        session_info.step_sort_jobs = [Job(i0 + steps, -1)]
        pass

def full_bubblesort_gen(chart_info: VisualState, session_info: InternalState):

    generator = bubble_sort_iterative(chart_info)
    
    try:
        while True:
            yield next(generator)
            
    except StopIteration:
        pass




# Step-sort
def step_quicksort_gen(
    chart_info: VisualState,
    session_info: InternalState,
    steps: int,
):

    generator = quick_sort_iterative(chart_info, session_info, step_sort=True, iterations_allowed = steps)
    
    try:
        while True:
            yield next(generator)
            
    except StopIteration:
        pass


def full_quicksort_gen(chart_info: VisualState, session_info: InternalState):

    # If pivot_alpha isn't 1, the sort function will unsort the array. This if statement will prevent that from happening
    if not is_sorted(chart_info.arr):

        generator = quick_sort_iterative(chart_info, session_info)

        try:
            while True:
                yield next(generator)
        except StopIteration:
            pass
        
    else:
        gr.Info("The array is fully sorted.")
        pass

def step_selectionsort_gen(chart_info: VisualState, session_info: InternalState, steps: int):
    
    # To follow the structure that session_info was built around, we use step_sort_jobs: list[Job] to store data for stepsort. We use a singular job in the list, and use that job's i0 as the point where the stepsort left off.
    if session_info.step_sort_jobs:
        current_job = session_info.step_sort_jobs.pop()
        i0 = current_job.i0
    else:
        i0 = 0

    generator = selection_sort_iterative(chart_info, start=i0, end=i0 + steps)

    try:
        while True:
            yield next(generator)
    except StopIteration:
        session_info.step_sort_jobs = [Job(i0 + steps, -1)]
        pass

def full_selectionsort_gen(chart_info: VisualState, session_info: InternalState):

    generator = selection_sort_iterative(chart_info)
    
    try:
        while True:
            yield next(generator)
    except StopIteration:
        pass


# Dictionary of algorithms; index 0: stepsort: stepsort generator, index 1: fullsort generator

sort_algorithms: dict[str, list[Any]] = {
    # <str>: [<step sort generator>, <full sort generator>],
    "Quick-Sort": [step_quicksort_gen, full_quicksort_gen],
    "Selection-Sort": [step_selectionsort_gen, full_selectionsort_gen],
    "Bubble-Sort": [step_bubblesort_gen, full_bubblesort_gen],
}

# END OF GRADIO HANDLERS

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

    algorithm_option = gr.Dropdown(choices=list(sort_algorithms.keys()), value=session_info_state.value.algorithm)
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


    
    
    # Both of these event handlers choose a sort function based on the current session_info.algorithm
    # These functions have different generators and generator arguments, but aside from that have the exact same logic
    async def step_button_on_click(
            chart_info: VisualState,
            session_info: InternalState,
            step_count: float # This has been made to be received as an int, but I'm leaving the parsing as a redundancy.
        ):

        
        lock = session_info.new_lock()
        generator = sort_algorithms[session_info.algorithm][0](chart_info, session_info, round(step_count))

        try:
            while session_info.is_lock_owner(lock):
                job_finished = next(generator)

                if session_info.show_queries:
                    if chart_info.swapping and chart_info.animate_swaps:

                        applied_wait_interval = session_info.wait_interval * chart_info.get_wait_multiplier_for_current_state()

                        chart_info.dt = applied_wait_interval
                        yield chart_info.to_embedded_json()
                        await wait(applied_wait_interval)

                    elif chart_info.swapping or session_info.show_comparisons:

                        applied_wait_interval = session_info.wait_interval

                        chart_info.dt = applied_wait_interval

                        yield chart_info.to_embedded_json()
                        await wait(applied_wait_interval)
                        
                elif job_finished:
                    chart_info.partitioning = True
                    yield chart_info.to_embedded_json()
                    chart_info.partitioning = False
                    await wait(session_info.wait_interval)

                # try:
                #     while session_info.is_lock_owner(lock):
                #         # job_finished is a bool that stores whether a job was completed on this yield
                #         job_finished = next(generator)
                #         
                        
                # except StopIteration:
                #     pass

                yield chart_info.to_embedded_json()
        except StopIteration:
            pass
            
            
        yield chart_info.to_embedded_json() # (Assumption based on debugging) At least one yield is required, otherwise chart_info_state.value is set to null
        session_info.close_lock(lock)

    async def sort_button_on_click(
            chart_info: VisualState,
            session_info: InternalState
        ):


        lock = session_info.new_lock()

        # Assumption is that 'full_sort_algorithms' is a dictionary that stores all the supported sort functions
        generator = sort_algorithms[session_info.algorithm][1](chart_info, session_info)

        try:
            while session_info.is_lock_owner(lock):
                job_finished = next(generator)

                if session_info.show_queries:
                    if chart_info.swapping and chart_info.animate_swaps:

                        applied_wait_interval = session_info.wait_interval * chart_info.get_wait_multiplier_for_current_state()

                        chart_info.dt = applied_wait_interval
                        yield chart_info.to_embedded_json()
                        await wait(applied_wait_interval)

                    elif chart_info.swapping or session_info.show_comparisons:

                        applied_wait_interval = session_info.wait_interval

                        chart_info.dt = applied_wait_interval

                        yield chart_info.to_embedded_json()
                        await wait(applied_wait_interval)
                        
                elif job_finished:
                    chart_info.partitioning = True
                    yield chart_info.to_embedded_json()
                    chart_info.partitioning = False
                    await wait(session_info.wait_interval)
        except StopIteration:
            pass

        yield chart_info.to_embedded_json() # (Assumption based on debugging) At least one yield is required, otherwise chart_info_state.value is set to null
        session_info.close_lock(lock)
                
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

    sort_button.click(sort_button_on_click, [
        chart_info_state,
        session_info_state,
    ], [hidden_graph_data], queue=True, concurrency_limit=None, )

    def algorithm_option_on_change(session_info: InternalState, new_algorithm: str):
        session_info.algorithm = new_algorithm
        # Cancel any running algorithms
        session_info.close_lock(session_info.new_lock())
    algorithm_option.change(algorithm_option_on_change, [session_info_state, algorithm_option])

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