# Features Layer

This directory contains **optional features** that can be enabled or disabled independently.

## Architecture

```
features/
├── self-healing/          # Self-healing system with memory compression
├── memory-compression/    # Memory management and compression
└── workflow-enforcement/  # Enhanced workflow enforcement
```

## Feature Management

Use the `ce-feature.sh` script to manage features:

```bash
# List all features
./scripts/ce-feature.sh list

# Enable a feature
./scripts/ce-feature.sh enable self-healing

# Disable a feature
./scripts/ce-feature.sh disable memory-compression

# Show feature details
./scripts/ce-feature.sh show workflow-enforcement
```

## Feature Structure

Each feature directory should contain:

```
feature-name/
├── __init__.py           # Feature entry point
├── README.md            # Feature documentation
├── config.yml           # Feature configuration
├── requirements.txt     # Feature dependencies (optional)
└── src/                 # Feature implementation
```

## Core Principle

**Features are optional** - the system runs without them. They can be:
- ✅ Installed/uninstalled anytime
- ✅ Enabled/disabled without restart
- ✅ Developed independently
- ❌ Cannot modify core/ files
- ❌ Cannot break core functionality

## Version: 2.0.0
