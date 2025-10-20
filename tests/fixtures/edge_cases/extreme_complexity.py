# tests/fixtures/edge_cases/extreme_complexity.py
"""
Sample code with extremely high complexity for testing.

This file intentionally contains code with high cyclomatic complexity
to test the complexity calculator's ability to detect problematic code.
"""


def extremely_complex_function(a, b, c, d, e, f, g):
    """
    Intentionally complex function for testing.

    Cyclomatic Complexity: ~20 (far exceeds threshold of 10)
    This should trigger quality warnings.
    """
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        if f > 0:
                            if g > 0:
                                return a + b + c + d + e + f + g
                            else:
                                return a + b + c + d + e + f
                        else:
                            return a + b + c + d + e
                    else:
                        return a + b + c + d
                else:
                    return a + b + c
            else:
                return a + b
        else:
            return a
    else:
        return 0


def moderately_complex_function(x, y, z):
    """
    Moderately complex function.

    Cyclomatic Complexity: ~6 (acceptable but approaching threshold)
    """
    result = 0

    if x > 0:
        result += x

    if y > 0:
        result += y
    elif y < 0:
        result -= y

    if z > 0:
        result *= z
    elif z < 0:
        result /= abs(z)

    return result


def simple_function(value):
    """
    Simple function with low complexity.

    Cyclomatic Complexity: 1 (ideal)
    """
    return value * 2


# Example of function that is too long (>50 lines)
def very_long_function():
    """
    Function that exceeds length threshold.

    This function has 60+ lines, exceeding the 50-line threshold.
    """
    result = []

    # Line 10
    for i in range(100):
        temp = i * 2

        # Line 15
        if temp % 2 == 0:
            result.append(temp)
        else:
            result.append(temp + 1)

        # Line 20
        if temp % 3 == 0:
            result.append(temp // 3)

        # Line 25
        if temp % 5 == 0:
            result.append(temp // 5)

        # Line 30
        for j in range(10):
            result.append(i + j)

        # Line 35
        if i > 50:
            result.append(i - 50)

        # Line 40
        if i < 50:
            result.append(i + 50)

        # Line 45
        temp_sum = 0
        for k in range(i):
            temp_sum += k

        # Line 50
        result.append(temp_sum)

        # Line 55
        if temp_sum > 100:
            result.append(temp_sum // 100)

        # Line 60
        result.append(temp * temp)

    # Line 65
    return result


# Excessive nesting depth (>4 levels)
def deeply_nested_function():
    """
    Function with excessive nesting depth.

    Nesting Depth: 5 (exceeds threshold of 4)
    """
    for i in range(10):  # Level 1
        if i > 0:  # Level 2
            for j in range(10):  # Level 3
                if j > 0:  # Level 4
                    for k in range(10):  # Level 5 - TOO DEEP
                        if k > 0:
                            print(f"{i}, {j}, {k}")
