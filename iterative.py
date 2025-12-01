def divide_and_sort(arr: [int], start: int, end: int, iterate=None) -> int:
    
    length = end - start

    pivot_value = arr[end]
    
    free_index = start

    for i in range(start, end):
        # check if this element is smaller than the pivot. If it is, then an index is taken up.
        if arr[i] <= pivot_value:
            # Swap the current element with the element at the insertion index. The element at the insertion index will always be larger than the pivot
            arr[free_index], arr[i] = arr[i], arr[free_index]

            # Call this function on iteration
            if iterate != None and i != free_index:
                iterate(arr, i, free_index)
            # Increment the variable for the next free index
            free_index += 1
        

    # Move the pivot element (which was retrieved with arr[end]) to the free index that was found, swapping with the current element in the free index
    arr[end], arr[free_index] = arr[free_index], pivot_value

    # Call this function on iteration
    if iterate != None and end != free_index:
        iterate(arr, end, free_index)

    # Return the free index, which has the position of the sorted element, the pivot
    return free_index

# There is no built-in type annotation for a function in python, but the 'iterate' parameter is meant to be for an update function
def quick_sort(arr: [int], start: int = 0, end: int | None = None, iterate=None) -> [int]:
    # Dynamic default value for the end-point
    end = end == None and len(arr) - 1 or end
    
    # Base case: The sub-array has reached length <= 1
    if start >= end:
        return
    
    # Get the pivot point's index
    pivot_point = divide_and_sort(arr, start, end, iterate=iterate)

    # Sort items below the pivot point's index
    quick_sort(arr, start, pivot_point - 1, iterate=iterate)
    # Sort items above the pivot point's index
    quick_sort(arr, pivot_point + 1, end, iterate=iterate)

    return arr



def show_result(arr, *indexes):
    result = "Swap: "
    for i in indexes:
        result += f"[{i}]: {arr[i]}, "
    print(result)
        

import random as rand
my_array = []

for i in range(1000):
    my_array.append(rand.randint(1,1000))

print(my_array)
print(quick_sort(my_array, iterate=show_result))