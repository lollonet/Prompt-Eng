# Idiomatic Python

Idiomatic Python refers to writing Python code in a way that is natural, efficient, and follows the conventions and best practices of the Python community. It's about leveraging Python's unique features and philosophies.

## Key Aspects:

*   **List Comprehensions:** Prefer list comprehensions over `for` loops for creating new lists based on existing iterables.
    *   `[x*2 for x in range(5)]` instead of `my_list = []; for x in range(5): my_list.append(x*2)`
*   **Generators:** Use generators for large datasets or infinite sequences to save memory.
*   **Context Managers (`with` statement):** Use `with` statements for resources that need proper setup and teardown (e.g., files, locks).
    *   `with open('file.txt', 'r') as f:`
*   **Decorators:** Use decorators for adding functionality to functions or methods without modifying their structure.
*   **`enumerate` for Iteration:** When iterating with an index, use `enumerate`.
    *   `for i, item in enumerate(my_list):`
*   **`zip` for Parallel Iteration:** Use `zip` to iterate over multiple iterables in parallel.
    *   `for a, b in zip(list1, list2):`
*   **`collections` Module:** Leverage specialized container datatypes like `defaultdict`, `Counter`, `namedtuple`.
*   **`f-strings` for String Formatting:** Prefer f-strings for clear and concise string formatting.
    *   `f"Hello, {name}!"`
*   **EAFP (Easier to Ask for Forgiveness than Permission):** Prefer `try-except` blocks over checking conditions beforehand.
    *   `try: value = my_dict[key] except KeyError:`
*   **Duck Typing:** Focus on what an object *can do* rather than what *type* it is.

Writing idiomatic Python makes your code more Pythonic, concise, and often more performant.