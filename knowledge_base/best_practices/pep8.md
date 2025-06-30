# PEP 8: Style Guide for Python Code

PEP 8 is the official style guide for Python code. Adhering to PEP 8 improves the readability and consistency of Python code, making it easier for others (and your future self) to understand and maintain.

## Key Principles:

*   **Readability:** Code is read much more often than it is written. Write code that is easy to read.
*   **Consistency:** Be consistent within a project. If a project already has a style, stick to it.

## Common Guidelines:

1.  **Indentation:** Use 4 spaces per indentation level.
2.  **Line Length:** Limit all lines to a maximum of 79 characters.
3.  **Blank Lines:** Use blank lines to separate logical sections of code.
    *   Two blank lines before top-level function and class definitions.
    *   One blank line before method definitions.
4.  **Imports:** Imports should usually be on separate lines.
    *   `import os`
    *   `import sys`
    *   Imports are always put at the top of the file, just after any module comments and docstrings, and before module globals and constants.
5.  **Whitespace in Expressions and Statements:** Avoid extraneous whitespace.
    *   `spam(1)` instead of `spam (1)`
    *   `dict['key'] = list[index]` instead of `dict ['key'] = list [index]`
6.  **Naming Conventions:**
    *   `lowercase_with_underscores` for functions, methods, variables.
    *   `CapitalizedWords` for class names.
    *   `ALL_CAPS_WITH_UNDERSCORES` for constants.
    *   `_single_leading_underscore` for internal use.
    *   `__double_leading_underscore` for name mangling.

Adhering to PEP 8 ensures your Python code is idiomatic and easily understood by the wider Python community.