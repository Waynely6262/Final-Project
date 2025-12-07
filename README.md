# CISC 121 Final Project

## Demonstration



### Step 1 - Choose an Algorithm & Justification
For this project, I chose quick-sort. It is the only algorithm that wasn't covered in high school. This algorithm sorts elements in an interesting way, which makes it a good reason to create a visualization for it. 

Although quick-sort is the main sort implementation, since I had extra time I decided to implement the other sorting algorithms as well. **For the sake of marking however, the extra algorithms should be ignored if deemed too long to mark**. There is also **no dedicated documentation on the extra algorithms**. 

*Note that if the extra algorithms are marked, since the framework was built for quick-sort, some parts of the code are improvised (such as using only 1 valid index for only 1 Job() object in the "step_sort_jobs" attribute of InternalState).*

### Step 2 - Plan Using Computational Thinking

#### Decomposition
The quick-sort algorithm requires some components:
- A pivot element
- A partition helper function that receives a start and end index, which moves elements smaller than the pivot element to the left side of the array
- An iterator or recursive main function that keeps track of partitions that need to be done

The interface should support the following input, for some purpose:
- boolean input fields will allow the user to choose some options that modify the behaviour of the algorithm.
- Buttons will allow the user to communicate with the program to perform certain sequences of actions.


#### Pattern Recognition
Each time a new pivot is chosen, the same operation is performed. There should be some callable helper method that separates the main operation and this sub-operation.
The pivot element is always swapped with the end of the array to avoid affecting the sorting process.


#### Abstraction
Every time the array is updated, the visualization should update based on the indexes that were changed.
- The user should be able to see the order of the elements in the array. Each element should be easily differentiable.
- The user should be able to see what the algorithm is currently evaluating, such as which two elements are being compared.
- Because the browser-end has to receive data, instead of constructing the HTML server-side, it should be constructed on the client-side using raw chart data, which is a lot smaller in size. This will avoid unnecessary data usage.

#### Algorithm Design

User input uses the following datatypes:
- Integer
- Float
- Boolean
- String


##### PYTHON (SERVER) DATATYPES, STRUCTURES & CLASSES:
The arrays subject to sorting are integer lists.
The program uses iteration instead of recursion in some places.
Multiple classes are defined:
- Job
- VisualState
- InternalState

##### JAVASCRIPT (CLIENT) DATATYPES, STRUCTURES & CLASSES:
In short, the JS side uses datatypes that best correspond to what the Python end uses:
- PY List -> Array
- PY Dictionary -> JS Object
- PY Object -> PY Dictionary -> JS Object
Linked lists are used for implementation of a queue class.

##### FRONT-END FLOWCHART

##### Input
The two state objects will be used as the main inputs for event handlers. This is because the state objects maintain their references for mutable objects, which allows dynamic changes to sorting behaviour.
- A State object "session_info" (InternalState) will keep track of back-end elements (elements that the server uses and the client-side doesn't need).
- A State object "chart_info" (VisualState) will keep track of front-end elements (elements that the client-side needs).
  
Most input fields that are used for sorting will have their values stored in the "session_info" State object everytime their values are changed.
Some input fields that don't affect the sorting algorithm itself (such as shuffle strength for the "shuffle" button) are directly specified as input for relevant event handlers.

##### Processing
Major processes include actions that directly modify the array and/or update the HTML data component.
- Major processes are only run after a button is pressed.
  - There is one button that does not run a major process: "Save Snapshot"
- To avoid overlapping major processes, most major processes use an ownership feature, which is implemented as part of session_info (the InternalState class), where processes increment a counter then take a snapshot of it. Once the snapshot doesn't match the counter, the process knows that another process was started and will perform clean-up and exit safely.

A minor process is a process that may or may not indirectly (for example through the editting of some attribute of session_info) modify the behaviour of major processes.
Minor processes include:
- Updating session_info based on some input field (slider, checkbox, radio)
- Storing a snapshot of the current array

##### Output
Output comes in the form of:
- gradio.Info() method that uses the gradio API to display messages
- The chart that contains all the bars in the graph
  
###### gradio.Info
gradio.Info() is called by some functions that need to inform the user on something that has happened internally.

###### JavaScript
The HTML data component with element id "graph-data" is updated to store a JSON copy of the "chart_info" State object's values.
The Javascript side listens to mutations on this HTML component. Every time a mutation has occurred on the HTML data component, javascript will act.
Mutations on the HTML component that arrive within the same frame will be stored in a frame queue, unless the queue-data option is set to false. 
If the latest data has queue-data set to false, the entire queue is cleared, and the latest data is enqueued.

The javascript side uses the data (all the attributes of VisualState) stored in the "graph-data" DOM element to construct the chart and run animations.
- The javascript side identifies the div for displaying the graph based on the element id "graph".
- Animations are run using easing functions, delta-time and lerping. Easing functions were taken from <link>https://easings.net</link>
- Bar widths are calculated based on available pixels to distribute and the array size.
- Bar widths are calculated every time the chart is rerendered. To optimize, calculations are memoized with array size.

The program supports the simple animation of two elements swapped on a fixed axis.

### Step 5: Test & Verify

Various inputs were tested, which helped to identify errors.

#### Notable Bugs
- PY: the implementation of 'insertion sort', where bounds for the sort were mixed up or off by 1. (approximate hours wasted: 0.6)
- JS: Properly cloning and placing the bars from the original chart div to the overlay div for animation (approximate hours wasted: 4)
- JS: Animation of bars, where the original bar would flash for a quick second on huggingface, but not in local environment (approximate hours wasted: 3)



## Steps to Run

### Default
Default settings allow the user to run the sort immediately:
- Press the "Complete Sort" button to completely sort the array
- Press the "Step" button to run one section of the sort.

### Tutorial

On smaller screens, reduce the number of elements with the "Total Elements" slider, and press "Regenerate Elements" until the graph is visible. 

#### Quick Demo
- Press the "Complete Sort" button at the bottom right of the page.
- If the sort is too slow, reduce the "Iteration Interval".
- Once the sort is finished, press the "Regenerate Elements" button or the "Shuffle Elements" button.
#### Stepping
- Repeatedly press the "Step" button at the bottom left of the page, until the array is fully sorted.
#### Quicksort Bad Cases
- Set the "Shuffle Strength" to 0.01 or some small number.
- Press the "Shuffle Elements' button until at least one element is out of place.
- Press Complete Sort and wait for the sort to finish.
#### Quicksort Good Case 1
- Enable "Use Random Pivot".
- Press the "Regenerate Elements" button.
- Press Complete Sort and wait for the sort to finish
#### Quicksort Good Case 2
- Disable "Use Random Pivot"
- Set "Custom Pivot Point" to 0.5
- Note: Make sure the array is sorted at this point (Assuming you just finished quicksort good case 1)
- Press Complete Sort and wait for the sort to finish
#### Brute Force
- Set "Total Elements" to 2000
- Press the "Regenerate Elements" button
- Set "Iteration Interval" to 0.001
- Set "Queue Data" to false
- Set "Show Comparisons" to false
- Optional: Set "Animate Swaps" to false
- Press the "Complete Sort" and wait for the sort to finish.
- If the program is taking too long, refresh the page and skip this task.

#### Other Sorts
- Select a different sorting algorithm
- Experiment with "Step" and "Complete Sort" on these algorithms
End of tutorial, have fun playing around!

### API
- The "Sort Algorithm" Radio allows the user to choose a sorting algorithm to run.

- "Complete Sort" will sort the entire array.
- "Step" will run a part of the sorting algorithm. Use the "Iterations per Step" slider to modify how many steps are performed.
- "Iterations per Step" controls how many steps are run when the "Step" button is pressed.
- "Stop Sorting" will stop any active sorting activities. This may not respond immediately because the client-side could still be receiving and/or processing outdated information
- "Queue Data" is an optimization option. When set to off, the iteration interval can be lowered further than 60 Hz, to 1000 Hz. Keep in mind that if outdated data is dropped, so animation will not run properly.
  
- "Show Queries" tells the program whether to show swaps and comparisons or not. This feature allows the user to quickly see the partitions made by the quick-sort algorithm.
- "Show Comparisons" tells the program to render the chart with highlighted elements every time the program compares two elements.
- "Animate Swaps" tells the program whether or not to animate swaps. If off, a green highlight is used to indicate which elements are swapped instead.
  
- "Regenerate Elements" will regenerate the array. To change the number of elements in the array, use the "Total Elements" slider.
- "Total Elements" slider lets the "Regenerate Elements" button know how many elements to include in the new array.
- "Shuffle Elements" will shuffle elements in the array. This can be done while the array is shuffling, but the algorithm will simply continue instead of accounting for it. To modify how strongly the the array is shuffled, use the "Shuffle Strength" slider. 0 means none of the elements are shuffled. 1 means all the elements are shuffled.
- "Shuffle Strength" slider controls the chance of an individual element being shuffled, with 0 being 0% and 1.0 being 100%.
- "Create Save Point" will allow the user to store a snapshot of the array, which can be loaded using the "Load Save Point" button.

- (QUICKSORT ONLY) "Use Random Pivot" will allow the quick-sort algorithm to choose a random pivot instead of a set pivot.
- (QUICKSORT ONLY) "Custom Pivot Point" will tell the program where to choose a pivot.


