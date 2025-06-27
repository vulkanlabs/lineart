# Workflow Nodes

## Overview

Workflow nodes are the fundamental building blocks of workflows in the Vulkan system. Each node represents a discrete step in a data processing or business logic pipeline and can be thought of as a function that executes in an isolated environment. Nodes form the vertices of a Directed Acyclic Graph (DAG), where dependencies between nodes represent the edges.

## Core Concepts

### What is a Node?

A node is a self-contained unit of execution that:
- Has a unique name and type
- Declares its dependencies on other nodes
- Can accept input data from dependent nodes
- Produces output data for subsequent nodes
- Executes specific logic based on its node type

### Node Dependencies

Nodes communicate with each other through a dependency system. Dependencies define how data flows between nodes and can be specified in three ways:

1. **Entire Node Output**: `Dependency("node_name")` - Uses the complete output of the specified node
2. **Specific Output Branch**: `Dependency(node="node_name", output="branch_name")` - Uses a specific output from branching nodes
3. **Dictionary Key Access**: `Dependency(node="node_name", key="key_name")` - Accesses a specific key from a node that returns a dictionary

### Node Hierarchy

Nodes can be organized in hierarchical structures, allowing for modular workflow composition and better organization of complex workflows.

## Node Types

The system supports eight distinct types of nodes, each serving a specific purpose in workflow execution:

### 1. Input Node

**Purpose**: Defines the entry point and input schema for a workflow.

**Key Characteristics**:
- Always the first node in any workflow, policy, or component
- Automatically added by the engine (not declared by users)
- Validates input data against a defined schema
- Provides a mechanism for users to pass data into the workflow

**Use Cases**:
- Workflow initialization
- Input validation
- Data entry points for external systems

### 2. Data Input Node

**Purpose**: Fetches data from external data sources and introduces it into the workflow.

**Key Characteristics**:
- Connects to pre-configured external data sources
- Supports runtime parameters for customized data fetching
- Acts as a bridge between external systems and the workflow
- Can be configured with specific parameters to control data retrieval

**Use Cases**:
- Loading data from databases
- Fetching information from APIs
- Reading files from storage systems
- Integrating external data feeds

### 3. Transform Node

**Purpose**: Executes arbitrary functions to process, manipulate, or transform data.

**Key Characteristics**:
- Most flexible node type for custom logic
- Executes user-defined functions with serializable code
- Receives dependencies as function parameters
- Provides execution context for logging and monitoring
- Can perform any computation that can be serialized

**Use Cases**:
- Data transformation and manipulation
- Mathematical calculations
- Data validation and cleaning
- Format conversions
- Business logic implementation

### 4. Branch Node

**Purpose**: Implements conditional logic to determine workflow execution paths.

**Key Characteristics**:
- Executes user-defined functions to make branching decisions
- Uses function output to select exclusive execution branches
- Requires predefined list of possible output choices
- Enables dynamic workflow routing based on data or conditions

**Use Cases**:
- Conditional workflow routing
- A/B testing scenarios
- Error handling paths
- Dynamic process selection
- Business rule branching

### 5. Decision Node

**Purpose**: Provides template-based conditional branching using if-else logic.

**Key Characteristics**:
- Uses Jinja2 template expressions for condition evaluation
- Implements structured if-else decision trees
- Must include at least one "if" and one "else" condition
- Supports multiple conditional branches

**Use Cases**:
- Simple conditional logic
- Template-based decision making
- Rule-based routing
- Configuration-driven branching

### 6. Connection Node

**Purpose**: Performs HTTP requests to external APIs and web services.

**Key Characteristics**:
- Supports all standard HTTP methods (GET, POST, PUT, DELETE, etc.)
- Configurable headers, parameters, and request body
- Built-in retry mechanisms
- Timeout handling
- Multiple response type support

**Use Cases**:
- API integrations
- Web service calls
- External system notifications
- Data synchronization
- Third-party service interactions

### 7. Terminate Node

**Purpose**: Marks the end of workflow execution and defines final outcomes.

**Key Characteristics**:
- Required as the final node in all workflow paths
- Returns a status code or final decision
- Can include metadata about the workflow execution
- Supports optional cleanup callbacks
- All leaf nodes must be terminate nodes

**Use Cases**:
- Workflow completion signaling
- Final status reporting
- Cleanup operations
- Result aggregation
- External system notifications about completion

### 8. Policy Node

**Purpose**: References and executes predefined policies within workflows.

**Key Characteristics**:
- References external policy definitions by ID
- Enables policy reuse across multiple workflows
- Supports modular workflow composition
- Maintains separation between policy definition and execution

**Use Cases**:
- Policy enforcement
- Reusable business logic
- Compliance checking
- Standardized decision making
- Modular workflow components

## Node Metadata

Each node type maintains specific metadata that defines its configuration and behavior:

- **Input Nodes**: Schema definitions for data validation
- **Data Input Nodes**: Data source configuration and parameters
- **Transform/Branch Nodes**: Source code for user-defined functions
- **Decision Nodes**: Condition definitions and decision logic
- **Connection Nodes**: HTTP request configuration
- **Terminate Nodes**: Return status and metadata specifications
- **Policy Nodes**: Policy reference identifiers

## Workflow Structure

A complete workflow must:
1. Start with an Input Node (automatically provided)
2. Include one or more processing nodes (Transform, Data Input, Connection, etc.)
3. End with Terminate Nodes on all execution paths
4. Form a valid Directed Acyclic Graph (DAG) structure
5. Have properly defined dependencies between nodes

This node-based architecture provides a flexible and powerful framework for building complex data processing and business logic workflows while maintaining clear separation of concerns and enabling modular composition.
