# Checklist of failure test cases

## Resource Creation

### General
- [X] Unauthorized access to create resources
- [X] Missing file: pyproject.toml
- [X] Missing imported python dependency (in pyproject.toml)

### Component Creation
- [X] Component name already exists
- [X] Component version name already exists
- [X] No ComponentDefinition
- [X] More than one ComponentDefinition
- [X] Missing required node
- [X] Dangling node

### Policy Creation

- [X] No PolicyDefinition
- [X] More than one PolicyDefinition
- [X] Missing required component 
- [X] Missing required node
- [X] Dangling node
- [X] Missing file: vulkan.yaml

## Runs

### Vulkan-specific

- [X] Invalid Policy ID
- [X] Unauthorized access to trigger run
- [X] Missing input

## Backtest

