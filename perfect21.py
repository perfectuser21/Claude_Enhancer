#!/usr/bin/env python3
"""
Perfect21 - Simple Rules for Better AI Coding
This is just a reference implementation showing how the rules work.
Claude Code should follow these patterns automatically via hooks.
"""

import yaml
from pathlib import Path

def load_rules():
    """Load agent selection rules"""
    rules_file = Path(__file__).parent / "rules" / "agent_rules.yaml"
    with open(rules_file, 'r') as f:
        return yaml.safe_load(f)

def suggest_agents(task_description):
    """Suggest agents based on task description"""
    rules = load_rules()
    task_lower = task_description.lower()

    for task_type, config in rules['task_patterns'].items():
        for keyword in config['keywords']:
            if keyword in task_lower:
                print(f"\n✅ Task type identified: {task_type}")
                print(f"📋 Required agents: {config['required_agents']}")
                print(f"🔢 Minimum count: {config['min_count']}")
                print(f"⚡ Execution: Parallel (all in one function_calls block)")
                return config['required_agents']

    # Default suggestion
    print("\n📋 Using default agent combination")
    print("🔢 Minimum: 3 agents")
    return ["backend-architect", "test-engineer", "code-reviewer"]

def main():
    """Simple demo of Perfect21 rules"""
    print("=" * 60)
    print("Perfect21 - Simple Rules for Better AI Coding")
    print("=" * 60)

    examples = [
        "Build a user login system",
        "Create an API for products",
        "Design database schema",
        "Build a React component",
        "Write comprehensive tests"
    ]

    for task in examples:
        print(f"\n🎯 Task: {task}")
        agents = suggest_agents(task)
        print(f"   Agents to use: {', '.join(agents[:3])}...")

    print("\n" + "=" * 60)
    print("Remember: These are just rules.")
    print("Claude Code does the actual work!")
    print("Hooks ensure the rules are followed automatically.")
    print("=" * 60)

if __name__ == "__main__":
    main()