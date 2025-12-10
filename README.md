---
title: Sort Visualizer - Waynely
emoji: 🔥
colorFrom: indigo
colorTo: gray
sdk: gradio
sdk_version: "6.0.0"
app_file: app.py
pinned: false
---
# CISC 121 Final Project

## Demonstration
Unfortunately due to lack of time, only a screenshot is available.
<img width="2457" height="1309" alt="image" src="https://github.com/user-attachments/assets/8bf1a381-34e5-451b-9f28-f3c3dc64ddeb" />

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

For the flowchart, only view good-copy for PYTHON
**Flowchart:** https://app.diagrams.net/#G1P_44fzNCCS08O1zV5GIMQivl4iAyn-WQ#%7B%22pageId%22%3A%224BXZXrdRpVA-gQ8RD3NR%22%7D


User input uses the following datatypes:
- Integer
- Float
- Boolean
- String


**PYTHON (SERVER) DATATYPES, STRUCTURES & CLASSES:**
The arrays subject to sorting are integer lists.
The program uses iteration instead of recursion in some places.
Multiple classes are defined:
- Job
- VisualState
- InternalState

**JAVASCRIPT (CLIENT) DATATYPES, STRUCTURES & CLASSES:**
In short, the JS side uses datatypes that best correspond to what the Python end uses:
- PY List → Array
- PY Dictionary → JS Object
- PY Object → PY Dictionary → JS Object  
Linked lists are used for implementation of a queue class.

**FRONT-END FLOWCHART**

**Input**
The two state objects will be used as the main inputs for event handlers. This is because the state objects maintain their references for mutable objects, which allows dynamic changes to sorting behaviour.
- A State object "session_info" (InternalState) will keep track of back-end elements (elements that the server uses and the client-side doesn't need).
- A State object "chart_info" (VisualState) will keep track of front-end elements (elements that the client-side needs).
  
Most input fields that are used for sorting will have their values stored in the "session_info" State object every time their values are changed.
Some input fields that don't affect the sorting algorithm itself (such as shuffle strength for the "shuffle" button) are directly specified as input for relevant event handlers.

**Processing**
Major processes include actions that directly modify the array and/or update the HTML data component.
- Major processes are only run after a button is pressed.
  - There is one button that does not run a major process: "Save Snapshot"
- To avoid overlapping major processes, most major processes use an ownership feature, which is implemented as part of session_info (the InternalState class), where processes increment a counter then take a snapshot of it. Once the snapshot doesn't match the counter, the process knows that another process was started and will perform clean-up and exit safely.

A minor process is a process that may or may not indirectly (for example through the editing of some attribute of session_info) modify the behaviour of major processes.
Minor processes include:
- Updating session_info based on some input field (slider, checkbox, radio)
- Storing a snapshot of the current array

**Output**
Output comes in the form of:
- gradio.Info() method that uses the gradio API to display messages
- The chart that contains all the bars in the graph
  
**gradio.Info**
gradio.Info() is called by some functions that need to inform the user on something that has happened internally.

**JavaScript**
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

#### Screenshots

**Testing Error Feedback**
<img width="1376" height="367" alt="testing error feedback handlers" src="https://github.com/user-attachments/assets/9aab7326-2cca-4dd1-859a-b54d312a4fcf" />
Issue: The defaulting except statement ("except Exception") would not provide details of the exception if triggered
  
Changes inspired: 
- Add "str(e)" to graph.js generalized exception message

**API Page View**
<img width="1225" height="839" alt="unclear splitting of different types of elements" src="https://github.com/user-attachments/assets/334b2bf8-6da4-479b-aea8-0248867bd3e9" />
Issue: unclear splitting of different types of elements

Changes inspired:
- Add headers to the subsections

## Steps to Run
On smaller screens, reduce the number of elements with the "Total Elements" slider, and press "Regenerate Elements" until the graph is visible. 

### Default
Default settings allow the user to run the sort immediately:
- Press the "Complete Sort" button to completely sort the array
- Press the "Step" button to run one section of the sort.

### Tutorial

#### Quick Demo
- Press the "Complete Sort" button at the bottom right of the page.
- If the sort is too slow, reduce the "Iteration Interval".
- Once the sort is finished, press the "Regenerate Elements" button or the "Shuffle Elements" button.

#### Stepping
- Repeatedly press the "Step" button at the bottom left of the page, until the array is fully sorted.

#### Quicksort Bad Cases
- Set the "Shuffle Strength" to 0.01 or some small number.
- Press the "Shuffle Elements" button until at least one element is out of place.
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

### API (sub-sections sorted by importance)

#### Algorithm
- The "Sort Algorithm" Radio allows the user to choose a sorting algorithm to run.


#### Sorting
- "Complete Sort" will sort the entire array.
- "Step" will run a part of the sorting algorithm. Use the "Iterations per Step" slider to modify how many steps are performed.
- "Iterations per Step" controls how many steps are run when the "Step" button is pressed.
- "Stop Sorting" will stop any active sorting activities. This may not respond immediately because the client-side could still be receiving and/or processing outdated information
- "Queue Data" is an optimization option. When set to off, the iteration interval can be lowered further than 60 Hz, to 1000 Hz. Keep in mind that if outdated data is dropped, the animation will not run properly.

#### View
- "Show Queries" tells the program whether to show swaps and comparisons or not. This feature allows the user to quickly see the partitions made by the quick-sort algorithm.
- "Show Comparisons" tells the program to render the chart with highlighted elements every time the program compares two elements.
- "Animate Swaps" tells the program whether or not to animate swaps. If off, a green highlight is used to indicate which elements are swapped instead.

#### Preparation
- "Regenerate Elements" will regenerate the array. To change the number of elements in the array, use the "Total Elements" slider.
- "Total Elements" slider lets the "Regenerate Elements" button know how many elements to include in the new array.
- "Shuffle Elements" will shuffle elements in the array. This can be done while the array is shuffling, but the algorithm will simply continue instead of accounting for it. To modify how strongly the array is shuffled, use the "Shuffle Strength" slider. 0 means none of the elements are shuffled. 1 means all the elements are shuffled.
- "Shuffle Strength" slider controls the chance of an individual element being shuffled, with 0 being 0% and 1.0 being 100%.
- "Create Save Point" will allow the user to store a snapshot of the array, which can be loaded using the "Load Save Point" button.
- "Load Save Point" will be available after "Create Save Point" is used. This button loads a saved array.

- (QUICKSORT ONLY) "Use Random Pivot" will allow the quick-sort algorithm to choose a random pivot instead of a set pivot.
- (QUICKSORT ONLY) "Custom Pivot Point" will tell the program where to choose a pivot.

## HUGGING FACE

https://huggingface.co/spaces/Waynely6262/sort-visualizer

## AUTHOR & ACKNOWLEDGEMENT

### HUMAN AUTHORS
Built by Wayne Bai (QU SID: 20553851)

### AI DISCLAIMER

ChatGPT-Auto was the only AI tool used

#### Links
- LinkedList implementation debug: https://chatgpt.com/share/6934cd4a-0100-8012-8a0b-a04b8b82435a

- General Chat: https://chatgpt.com/share/6934cfec-2600-8012-8ae0-cea945dd195d|

- Gradio Explanation & Example Code: https://chatgpt.com/share/6934d0ad-f1bc-8012-9d58-175090792066

- Explain requirements.txt: https://chatgpt.com/share/6934d011-c0d4-8012-82d1-a2621e6f2b46

- JavaScript Animation Chat: https://chatgpt.com/share/6934d036-b0fc-8012-bba6-f4767c3a0d7d

#### Breakdown
- AI Level 1 was used to explain the Gradio API
- AI Level 1 was used to explain basic asynchronous tasking in PY
- AI Level 2 was used to attempt to debug code (unfortunately, usually with little to no success)
- AI Level 3 was used to translate my knowledge in Luau (a scripting language) into JavaScript equivalents (such as requestAnimationFrame(lambda) & game["Run Service"].RenderSteppd.Once(self, lambda: (dt: number) -> ()).
- AI Level 3 was used to generate example code for concepts (inspired by but not used in the project).
- AI Level 4 was used to translate the "Color" class and some constants from Python into JavaScript.
- AI Level 4 was used to generate a DOM cloning function "copyElementToOverlay".
- AI Level 4 was used to regenerate this README file the exact way it was before, except "\#\#\#\#\# Header" occurrences are replaced with "\*\*Header\*\*"

#### Just For Fun
Test me in-person on how well I know the program's explicitly written logic (imported libraries don't count)!

