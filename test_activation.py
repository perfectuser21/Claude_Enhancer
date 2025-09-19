#!/usr/bin/env python3
"""Test file for hook activation"""

def hello_world():
    """Simple test function"""
    message = "Hello from Perfect21 hooks!"
    print(message)
    return message

if __name__ == "__main__":
    result = hello_world()
    print(f"Test successful: {result}")