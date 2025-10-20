#!/usr/bin/env python3
"""
Sample Python file with intentional code quality issues.
用于演示代码质量检查工具的示例文件（包含5种质量问题）
"""


def calculate_average(numbers):
    """Calculate the average of a list of numbers (GOOD example)."""
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)


# Issue 1: Bad naming (should be snake_case)
def CalculateSum(numbers):
    """Calculate sum (bad naming - PascalCase)."""
    return sum(numbers)


# Issue 2: Function too long (>50 lines)
def process_data_with_many_steps(data):
    """
    This function is intentionally too long.
    It should be refactored into smaller functions.
    """
    result = []

    # Step 1: Validate input
    if data is None:
        return None
    if not isinstance(data, list):
        return None
    if len(data) == 0:
        return []

    # Step 2: Clean data
    for item in data:
        if item is not None:
            if isinstance(item, str):
                item = item.strip()
                if item != "":
                    result.append(item)
            elif isinstance(item, int):
                if item > 0:
                    result.append(item)
            elif isinstance(item, float):
                if item > 0.0:
                    result.append(item)

    # Step 3: Sort data
    result.sort()

    # Step 4: Remove duplicates
    unique_result = []
    for item in result:
        if item not in unique_result:
            unique_result.append(item)

    # Step 5: Transform data
    final_result = []
    for item in unique_result:
        if isinstance(item, str):
            final_result.append(item.upper())
        else:
            final_result.append(item * 2)

    # Step 6: Add metadata
    output = {
        'data': final_result,
        'count': len(final_result),
        'processed': True
    }

    return output


# Issue 3: Deep nesting (>3 levels)
def check_nested_conditions(a, b, c, d):
    """Function with deep nesting."""
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    # Too deep nesting (depth = 4)
                    return "all positive"
                else:
                    return "d is not positive"
            else:
                return "c is not positive"
        else:
            return "b is not positive"
    else:
        return "a is not positive"


# Issue 4: Another bad naming
def BadFunctionName():
    """Bad naming convention."""
    pass


# Issue 5: Missing docstring
def no_docstring_function(x, y):
    return x + y


# GOOD example: Well-written function
def format_user_data(user: dict) -> str:
    """
    Format user data into a readable string.

    Args:
        user: Dictionary containing user information

    Returns:
        Formatted string representation of user data
    """
    name = user.get('name', 'Unknown')
    age = user.get('age', 0)
    email = user.get('email', 'N/A')

    return f"Name: {name}, Age: {age}, Email: {email}"
