import gradio as gr
from typing import Any, AsyncGenerator, Generator, Callable
from math import floor, log
import random as rand
from asyncio import sleep as wait
import json

# UTILS

# Ensures number n is between number l and number u
def clamp(n: float, l: float, u: float): # o(1) time
    if l > u:
        u,l=l,u
    return min(max(n, u), l)

# Principle equation for linear interpolation (and v0 + (v1-v0)*a, but I like this one because it feels cleaner) 
def lerp(v0: float, v1: float, a: float) -> float: # o(1) time
    return (1 - a) * v0 + (v1 * a)

# Checks if a list is sorted
def is_sorted(arr: list[int]): # o(n) time
    for i in range(1, len(arr)):
        if arr[i - 1] > arr[i]:
            return False
    return True

# Generates integers in a way specifically desgined for this program
def regenerate(arr: list[int], elements: int | None = 50): # o(n) time? (Not sure how long arr.clear() directly takes)
    if elements == None: elements = 50
    arr.clear()
    for _ in range(elements):
        arr.append(rand.randint(10,1000))
    return arr

# Fisher-Yates shuffle, with a shuffle_strength variable representing the percentage likelihood that an element will be swapped
def shuffle(arr: list[int], shuffle_strength: float=1.0): # o(n) time worst case
    for i in range(len(arr) - 1, 0, -1):
        if rand.random() > shuffle_strength: continue
        j = rand.randint(0, i)
        arr[i], arr[j] = arr[j], arr[i]
    return arr

# END OF UTILS

# UTILITY CLASSES (This used to be a slight bit longer) (Also feel free to optimize by removing the Job class entirely as it only serves as a start and end point, which can be represented by a tuple)
class Job:
    def __init__(self, start: int, end: int):
        self.i0 = start
        self.i1 = end
# END OF UTILITY CLASSES


# CONFIG (Optionally, create a config file so values are automatically shared by both sides)
# Make sure these matches the identifiers used in graph.js
HTML_DATA_HOLDER_ELEMENT_ID = "graph-data" # HTML element ID where the graph data JSON is stored
HTML_GRAPH_ELEMENT_ID = "graph" # HTML element ID where the graph will be rendered

# Chart Size
TOTAL_HEIGHT_PX = 200 # SYNC THIS WITH JS (OR CREATE A CONFIG FILE)
TOTAL_WIDTH_PX = 2000 # SYNC THIS WITH JS (OR CREATE A CONFIG FILE)
# Other
MAXIMUM_ELEMENTS_FOR_SHUFFLE_ANIMATION = 32 
# END OF CONFIG
MAX_ELEMENTS = TOTAL_WIDTH_PX


# CLASSES

class VisualState:
    arr: list[int]
    partitioning: bool = False
    i0: int = 0 # Lower interval index
    i1: int = 0 # Upper interval index
    pv: int | None = None # Pivot index
    s0: int | None = None # First swap index
    s1: int | None = None # Second swap index
    bulk_swap: list[tuple[int,int]] | None = None # A list of 2-element arrays for rendering multiple swaps at once: {[0] = s0, [1] = s1, [2] = dt}
    dt: float = 0 # Expected time delay before proceeding
    swapping: bool = False # Whether a swap is occurring. The swap indexes will be coloured differently if (swapping)
    animate_swaps: bool = True # Whether to animate swaps
    do_queue: bool = True # Whether to queue data sent to js or to drop other frames
    
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

        
    def convert_bulk_swap_attribute_to_antisymmetric_and_irreflexive(self):

        # For indices that swapped places, there will be (a,b) and (b,a). This will cause the animation to run the same thing.
        # This means, in discrete math terms:
        # Given the relation of R = {kEN, 0 <= k < len(chart_info.arr): (chart_info.s[k][0], chart_info.s[k][1])}
        # R must be antisymmetric.
        # R does not have to be irreflexive, but it can be done to optimize data transfer (sending (a,a) is useless and takes a couple bytes)
        
        if not self.bulk_swap: return
        pairs: dict[int, int] = {}
        # Iterate backwards so popping doesn't affect indexing
        for i in range(len(self.bulk_swap) - 1, -1, -1):

            relation: tuple[int,int] = self.bulk_swap[i]
            a = relation[0]
            b = relation[1]

            # Irreflexive
            if a == b:
                self.bulk_swap.pop(i)
                continue
            # Antisymmetric
            if b in pairs and pairs[b] == a:
                self.bulk_swap.pop(i)
                continue
            pairs[a] = b

    def get_wait_multiplier_for(self, s0: int, s1: int) -> float:
        return log(2 + abs(s0 - s1), 2)

    def get_wait_multiplier_for_current_state(self) -> float:
        if not self.animate_swaps: return 1 # The purpose of the delay was just to make sure the animation doesn't happen too quickly if elements are further apart. If animatiosn aren't happening, just use a multiplier of 1
        if not (self.s0 and self.s1): return 1
        return self.get_wait_multiplier_for(self.s0, self.s1)
    
    def to_embedded_json(self) -> str:
        json_src = json.dumps(self.__dict__)
        return f"<script id=\"{HTML_DATA_HOLDER_ELEMENT_ID}\" type=\"application/json\">{json_src}</script>"
    
    def clone(self):
        new_clone = VisualState()

        read = self.__dict__
        
        for k in read:
            v: Any = read[k]
            new_v = v
            if isinstance(v, list):
                new_v: list[Any] = []
                for j in range(len(v)):
                    new_v.append(v[j]) # deepcopying is not supported; I don't know enough python syntax, and it's not required here because this object's maximum depth is known

            setattr(new_clone, k, new_v)


        return new_clone
    
# bounded by 32-bit int lim.
START_CALL_ID = -2**31
MAX_CALL_ID = 2**31 - 1
class InternalState:

    is_active: bool = False # Whether sorting is active
    step_sort_jobs: list[Job] | None = None
    call_id: int = START_CALL_ID
    pv_alpha: float = 1.0

    wait_interval: float = 0.1

    use_random_pv: bool = False
    show_queries: bool = True
    show_comparisons: bool = True
    
    algorithm: str = "Quick-Sort"

    snapshot: VisualState | None = None

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

def shuffle_iterative(chart_info: VisualState, shuffle_strength: float=1.0):




    if len(chart_info.arr) < MAXIMUM_ELEMENTS_FOR_SHUFFLE_ANIMATION:
        # Tracer array, shuffles a set of indices, to be applied later so that animations don't animate on one object multiple times, since an element in the array can be displaced more than once
        indices: list[int] = []
        for i in range(len(chart_info.arr)):
            indices.append(i)
        shuffle(indices, shuffle_strength)

        # Don't need to set chart.swapping = True because the js side doesn't read this property, the swapping attribute is meant for the focused swap
        chart_info.bulk_swap = []        
        for final in range(len(indices)):
            initial = indices[final]
            new_2_ele: tuple[int,int] = (initial, final)
            chart_info.bulk_swap.append(new_2_ele)

        chart_info.dt = 1
        chart_info.convert_bulk_swap_attribute_to_antisymmetric_and_irreflexive() # Holy long identifier
        # Run the animation first
        yield
        # Update indices based on the antisymmetric and irreflexive data
        for i in range(len(chart_info.bulk_swap)):
            data = chart_info.bulk_swap[i]
            initial = data[0]
            final = data[1]
            chart_info.arr[initial], chart_info.arr[final] = chart_info.arr[final], chart_info.arr[initial]
        chart_info.bulk_swap = None
    else:
        shuffle(chart_info.arr, shuffle_strength)
        yield
def bubble_sort_iterative(chart_info: VisualState, start: int | None=None, end: int | None=None):

    l = len(chart_info.arr)

    chart_info.partitioning = True
    start = start or 0 # For 0, which is falsey: evaluate 'start'= 0 -> evaluate '0'= 0 -> result: 0, therefore making sure 'start' isn't 0 is redundant
    end = end or l # If end is 0, this thing doesn't run anyway so 0 is fine!

    chart_info.i0 = start
    
    for query_begin in range(start, min(l, end)):
        did_swap = False

        eoq = l - query_begin + start
        chart_info.i1 = eoq
        for query in range(eoq - 1):
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
        yield True
        if not did_swap:
            break

    chart_info.partitioning = False
                
        
def insertion_sort_iterative(chart_info: VisualState, start: int | None =None, end: int | None=None):

    chart_info.partitioning = True

    l = len(chart_info.arr)

    end = end != None and end or l

    free_index = start or 0

    chart_info.i0 = 0

    for i in range(free_index, min(l - 1, end)):
        chart_info.swapping = True
        chart_info.i1 = i + 1

        for self_i in range(i + 1, 0, -1):
            query_i = self_i - 1
            if chart_info.arr[query_i] <= chart_info.arr[self_i]:
                chart_info.swapping = False
                chart_info.s1 = None
                chart_info.s0 = None
                chart_info.pv = query_i
                yield True
                break
            # Subject's index is always going to be q + 1 because this loop will keep moving subject
            chart_info.s0 = query_i
            chart_info.s1 = self_i
            chart_info.pv = self_i
            yield
            chart_info.arr[query_i], chart_info.arr[self_i] = chart_info.arr[self_i], chart_info.arr[query_i]
        else:
            chart_info.swapping = False


                
        

        


# SELECTION SORT
def selection_sort_iterative(chart_info: VisualState, start: int | None=None, end: int | None=None):

    chart_info.partitioning = True

    l = len(chart_info.arr)
    final_index = l - 1

    chart_info.i1 = l

    end = end != None and end or final_index
    for i in range(start or 0, min(final_index, end)):
        chart_info.swapping = False
        chart_info.pv = i
        chart_info.i0 = i
        chart_info.s0 = i

        low_i = i
        low_v = chart_info.arr[i]
        # If the lower bound is greater than the upper bound, the loop just won't run, so we don't have to worry about it

        for q in range(i + 1, l):
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

# SORT GENERATORS (To assist in interfacing with Gradio components)

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
        next_index = i0 + steps
        if len(chart_info.arr) > next_index:
            session_info.step_sort_jobs = [Job(next_index, -1)]
        pass

def full_bubblesort_gen(chart_info: VisualState, session_info: InternalState):

    generator = bubble_sort_iterative(chart_info)
    
    try:
        while True:
            yield next(generator)
            
    except StopIteration:
        pass


# Insertion sort

def step_insertionsort_gen(chart_info: VisualState, session_info: InternalState, steps: int):

    if session_info.step_sort_jobs:
        current_job = session_info.step_sort_jobs.pop()
        i0 = current_job.i0
    else:
        i0 = 0

    generator = insertion_sort_iterative(chart_info, start=i0, end=i0 + steps)
    
    try:
        while True:
            yield next(generator)
            
    except StopIteration:
        next_index = i0 + steps
        if len(chart_info.arr) > next_index:
            session_info.step_sort_jobs = [Job(next_index, -1)]
        pass

def full_insertionsort_gen(chart_info: VisualState, session_info: InternalState):

    generator = insertion_sort_iterative(chart_info)
    
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
        
        next_index = i0 + steps
        if len(chart_info.arr) > next_index:
            session_info.step_sort_jobs = [Job(next_index, -1)]
        pass

def full_selectionsort_gen(chart_info: VisualState, session_info: InternalState):

    generator = selection_sort_iterative(chart_info)
    
    try:
        while True:
            yield next(generator)
    except StopIteration:
        pass


# Dictionary of algorithms; <str> indexes <tuple> where: index 0: stepsort: stepsort generator, index 1: fullsort generator

sort_algorithms: dict[str, list[Any]] = {
    # <str>: [<step sort generator>, <full sort generator>],
    "Quick-Sort": [step_quicksort_gen, full_quicksort_gen],
    "Selection-Sort": [step_selectionsort_gen, full_selectionsort_gen],
    "Bubble-Sort": [step_bubblesort_gen, full_bubblesort_gen],
    "Insertion-Sort": [step_insertionsort_gen, full_insertionsort_gen],
}

# END OF SORT GENERATORS

# Main

# Requires "graph,js"
try:
    with open("graph.js", "r") as js_file:
       graph_builder_src_js = js_file.read()
        # Load js source code
except FileNotFoundError:
    exit("Fatal error: could not finish build because required js logic \"graph.js\" is missing; Is it in the same directory as 'app.py'?")
except Exception as e:
    exit("Fatal error: could not finish build (Attempting to read \"graph.js\")")

with gr.Blocks() as demo:


    # INITIALIZE ELEMENTS

    # chart_info_state stores components relevant to updating the html bar chart.
    # This gr.State object is specified as "part of an event listener's output" whenever the event handler will update the chart info state.
    chart_info_state = gr.State(value=VisualState())
    
    # session_info_state stores components that are irrelevant to graphics: Essentially, values that are only used internally (in the back-end)
    # An assumption is made that type(gr.State()) objects pass their 'value' attribute whenever the gr.State object is used as input, meaning that references are maintained and session_info never needs to be used as output.
    session_info_state = gr.State(value=InternalState()) # luau typecheck: gr.State & {value: InternalState}

    gr.Markdown("# Sort Visualizer: by Wayne Bai (SID: 20553851)")

    # stores hidden data
    hidden_graph_data = gr.HTML(value=chart_info_state.value.to_embedded_json())

    # Initialize as empty because this element is updated on the client-side
    html_chart = gr.HTML(value=f"<div></div>", elem_id=HTML_GRAPH_ELEMENT_ID)

    # Which sorting algorithm to use
    algorithm_option = gr.Radio(label="Sort Algorithm", choices=list(sort_algorithms.keys()), value=session_info_state.value.algorithm)
    
    # Visual update controls
    with gr.Row():
        show_queries_option = gr.Checkbox(label="Show Queries", value=session_info_state.value.show_queries) # Uses session info because py prompts visual updates, so js doesnt need this
        show_comparisons_option = gr.Checkbox(label="Show Comparisons", value=session_info_state.value.show_comparisons) # Uses session info because py prompts visual updates, so js doesnt need this
        animate_swaps_option = gr.Checkbox(label="Animate Swaps", value=chart_info_state.value.animate_swaps) # Uses chart info because js needs to know whether to animate

    # Pivot controls
    with gr.Row():
        use_random_pv_option = gr.Checkbox(label="Use Random Pivot (quicksort)", value=session_info_state.value.use_random_pv)
        pv_alpha_slider = gr.Slider(label="Custom Pivot Point (quicksort)", minimum=0, maximum=1, value=1)

    # Unsorting controls
    with gr.Row():
        with gr.Column():
            element_count_slider = gr.Slider(label="Total Elements", minimum=1, maximum=MAX_ELEMENTS, value=50, step=1)
            reset_button = gr.Button("Regenerate Elements")
        with gr.Column():
            shuffle_strength_field = gr.Slider(label= "Shuffle Strength", minimum=0.0, maximum=1.0, value=0.1)
            shuffle_button = gr.Button("Shuffle Elements")
        with gr.Column():
            snapshot_button = gr.Button("Create Save Point")
            load_snapshot_button = gr.Button("Load Save Point", interactive=False)
            

    # Sorting controls
    with gr.Row():
        with gr.Column():
            iterations_per_step_slider = gr.Slider(label="Iterations per Step", minimum=1, maximum=10, value=1, step=1)
            step_button = gr.Button("Step")
        with gr.Column():
            queue_data_option = gr.Checkbox(label="Queue Data (Setting to false will improve responsiveness but skip steps, disable this for large arrays)", value=chart_info_state.value.do_queue)
            iteration_interval_slider = gr.Slider(label="Iteration Interval (seconds)", minimum=0.016, maximum=0.5, step=0.001, value=session_info_state.value.wait_interval)
            stop_button = gr.Button("Stop Sorting (May not respond immediately for large arrays)")
            sort_button = gr.Button("Complete Sort")

    # Load the README because why not
    try:

        with open("README.md", "r") as instructions_file:
            readme_src = instructions_file.read()
            gr.Markdown(readme_src)
    except Exception as e:
        print(f"Failed to load README instructions {str(e)}") 
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
        # Remove any step-sort jobs
        session_info.step_sort_jobs = None
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
    

    def queue_data_option_on_change(chart_info: VisualState, v: bool, iter_interval: float):
        chart_info.do_queue = v

        iteration_interval_lower_bound = v and 0.016 or 0.001

        # 'clamp' util is defined; if the upper bound is also variable, change this to clamp() instead of max()
        return gr.update(value=max(iter_interval, iteration_interval_lower_bound), minimum=iteration_interval_lower_bound)
    queue_data_option.change(queue_data_option_on_change, [chart_info_state, queue_data_option, iteration_interval_slider], [iteration_interval_slider])



    # Since this doesn't affect the number of elements in the list, it won't cause the program to fail. I will let this be callable mid-sort, just for fun
    def shuffle_button_on_click(chart_info: VisualState, shuffle_strength: float):

        # shuffle(chart_info.arr, shuffle_strength)


        # chart_info.reset_visuals() # This is disabled because it will modify chart_info.pv, which causes issues because the sort algorithm doesn't reset chart_info.pv even if it's currently active
        
        shuffle_generator = shuffle_iterative(chart_info, shuffle_strength)

        try:
            while True:
                next(shuffle_generator)
                chart_info.dt = 0.25*chart_info.get_wait_multiplier_for_current_state()
                yield chart_info.to_embedded_json()
        except StopIteration:
            pass

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


    # save point


    def snapshot_button_on_click(chart_info: VisualState, session_info: InternalState):
        session_info.snapshot = chart_info.clone()
        session_info.snapshot.reset_visuals()
        return gr.update(interactive=True)
    snapshot_button.click(snapshot_button_on_click, [chart_info_state, session_info_state], [load_snapshot_button])

    def load_snapshot_button_on_click(session_info: InternalState):
        gr.Info("Loading snapshot.. ")  
        session_info.close_lock(session_info.new_lock())
        # This button isn't interactable until snapshot_button_on_click is called, and it simultaneously asserts session_info.snapshot, therefore it is safe to read at this point
        yield session_info.snapshot.clone(), session_info.snapshot.to_embedded_json()
    load_snapshot_button.click(load_snapshot_button_on_click, [session_info_state], [chart_info_state, hidden_graph_data])


    # end of save point

demo.launch(share=True, head=f"<script defer>{graph_builder_src_js}</script>")
