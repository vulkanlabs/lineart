# Vulkan Workflow Specification

This document describes the JSON specification format for Vulkan workflows. This format serves as the unified interface between different ways of creating workflows (Python client, web UI, and AI copilot) and the core Vulkan engine.

## Overview

A Vulkan workflow is defined as a Directed Acyclic Graph (DAG) of nodes, where each node represents a step in the workflow execution. The workflow specification is a JSON document that describes:

1. **Nodes**: The processing steps in the workflow
2. **Dependencies**: How data flows between nodes
3. **Input Schema**: The expected input format for the workflow

## Workflow Structure

```json
{
  "nodes": [
    // Array of node definitions
  ],
  "input_schema": {
    // Input parameter definitions
  },
  "config_variables": [
    // Optional configuration variables
  ]
}
```

### Root Level Properties

- **`nodes`** (required): Array of node definitions that make up the workflow
- **`input_schema`** (required): Dictionary defining the input parameters and their types
- **`config_variables`** (optional): Array of configuration variable names

## Node Structure

Each node in the workflow follows this general structure:

```json
{
  "name": "string",              // Unique identifier for the node
  "node_type": "NODE_TYPE",      // Type of node (see Node Types section)
  "dependencies": {              // How this node depends on others
    "param_name": {
      "node": "source_node",
      "output": null,            // Optional: specific output branch
      "key": null,               // Optional: specific key from output
      "hierarchy": null          // Optional: hierarchy level
    }
  },
  "metadata": {                  // Node type-specific configuration
    // Varies by node type
  },
  "description": "string",       // Optional: human-readable description
  "hierarchy": ["level1"]        // Optional: hierarchy levels
}
```

### Node Properties

- **`name`**: Unique identifier for the node within the workflow
- **`node_type`**: Defines the behavior of the node (see Node Types below)
- **`dependencies`**: Dictionary mapping parameter names to their data sources
- **`metadata`**: Node type-specific configuration object
- **`description`**: Optional human-readable description
- **`hierarchy`**: Optional array of hierarchy levels for organizational purposes

## Dependencies

Dependencies define how data flows between nodes. Each dependency specifies:

```json
{
  "node": "source_node_name",    // Name of the source node
  "output": null,                // Optional: specific output branch
  "key": null,                   // Optional: specific key from output
  "hierarchy": null              // Optional: hierarchy level
}
```

### Dependency Types

1. **Full Node Output**: Uses the entire output of the source node
   ```json
   {"node": "source_node", "output": null, "key": null, "hierarchy": null}
   ```

2. **Specific Output Branch**: Uses a specific output from nodes with multiple outputs (e.g., decision nodes)
   ```json
   {"node": "decision_node", "output": "approved", "key": null, "hierarchy": null}
   ```

3. **Dictionary Key**: Accesses a specific key from the node's output dictionary
   ```json
   {"node": "api_node", "output": null, "key": "score", "hierarchy": null}
   ```

## Node Types

### CONNECTION

Makes HTTP requests to external APIs and services.

**Metadata Properties:**
```json
{
  "url": "string",                    // Required: API endpoint URL
  "method": "GET|POST|PUT|DELETE",    // HTTP method (default: "GET")
  "headers": {},                      // Optional: HTTP headers
  "params": {},                       // Optional: Query parameters
  "body": {},                         // Optional: Request body
  "timeout": 30,                      // Optional: Timeout in seconds
  "retry_max_retries": 1,            // Optional: Max retry attempts
  "response_type": "JSON|PLAIN_TEXT"  // Response format (default: "JSON")
}
```

**Example:**
```json
{
  "name": "credit_check",
  "node_type": "CONNECTION",
  "dependencies": {
    "inputs": {
      "node": "input_node",
      "output": null,
      "key": null,
      "hierarchy": null
    }
  },
  "metadata": {
    "url": "https://api.creditcheck.com/v1/check",
    "method": "POST",
    "headers": {
      "Authorization": "Bearer {{config.api_token}}",
      "Content-Type": "application/json"
    },
    "body": {
      "tax_id": "{{inputs.tax_id}}",
      "include_score": true
    },
    "timeout": 30,
    "retry_max_retries": 3,
    "response_type": "JSON"
  }
}
```

### DECISION

Evaluates conditions and routes workflow execution based on the results.

**Metadata Properties:**
```json
{
  "conditions": [
    {
      "decision_type": "if|else-if|else",  // Condition type
      "condition": "expression",           // Boolean expression (null for "else")
      "output": "output_name"             // Output branch name
    }
  ]
}
```

**Rules:**
- Must have at least one `"if"` condition
- Must have exactly one `"else"` condition
- Can have multiple `"else-if"` conditions
- Conditions are evaluated in order

**Example:**
```json
{
  "name": "risk_assessment",
  "node_type": "DECISION",
  "dependencies": {
    "score_data": {
      "node": "credit_check",
      "output": null,
      "key": null,
      "hierarchy": null
    }
  },
  "metadata": {
    "conditions": [
      {
        "decision_type": "if",
        "condition": "score_data.credit_score > 750",
        "output": "low_risk"
      },
      {
        "decision_type": "else-if",
        "condition": "score_data.credit_score > 600",
        "output": "medium_risk"
      },
      {
        "decision_type": "else",
        "condition": null,
        "output": "high_risk"
      }
    ]
  }
}
```

### TERMINATE

Marks the end of a workflow execution path and returns a final result.

**Metadata Properties:**
```json
{
  "return_status": "string",           // Final status/decision
  "return_metadata": {                 // Optional: Additional return data
    "key": {
      "node": "source_node",
      "output": null,
      "key": null,
      "hierarchy": null
    }
  }
}
```

**Example:**
```json
{
  "name": "approved",
  "node_type": "TERMINATE",
  "dependencies": {
    "condition": {
      "node": "risk_assessment",
      "output": "low_risk",
      "key": null,
      "hierarchy": null
    }
  },
  "metadata": {
    "return_status": "approved",
    "return_metadata": {
      "original_request": {
        "node": "input_node",
        "output": null,
        "key": null,
        "hierarchy": null
      },
      "credit_data": {
        "node": "credit_check",
        "output": null,
        "key": null,
        "hierarchy": null
      }
    }
  }
}
```

### TRANSFORM

Executes custom Python code to transform or process data.

**Metadata Properties:**
```json
{
  "source_code": "string"    // Python function source code
}
```

**Example:**
```json
{
  "name": "calculate_score",
  "node_type": "TRANSFORM",
  "dependencies": {
    "api_data": {
      "node": "credit_check",
      "output": null,
      "key": null,
      "hierarchy": null
    }
  },
  "metadata": {
    "source_code": "def transform(ctx, api_data):\n    # Calculate custom risk score\n    base_score = api_data.get('credit_score', 0)\n    risk_factors = api_data.get('risk_factors', [])\n    penalty = len(risk_factors) * 10\n    return max(0, base_score - penalty)"
  }
}
```

### BRANCH

Evaluates custom Python code to determine which execution path to follow.

**Metadata Properties:**
```json
{
  "choices": ["option1", "option2"],    // Array of possible output branches
  "source_code": "string"              // Python function source code
}
```

**Example:**
```json
{
  "name": "risk_branch",
  "node_type": "BRANCH",
  "dependencies": {
    "score": {
      "node": "calculate_score",
      "output": null,
      "key": null,
      "hierarchy": null
    }
  },
  "metadata": {
    "choices": ["low_risk", "high_risk"],
    "source_code": "def branch(ctx, score):\n    if score > 700:\n        return 'low_risk'\n    else:\n        return 'high_risk'"
  }
}
```

### DATA_INPUT

Fetches data from pre-configured external data sources.

**Metadata Properties:**
```json
{
  "data_source": "string",        // Name of configured data source
  "parameters": {}                // Optional: Runtime parameters
}
```

**Example:**
```json
{
  "name": "customer_data",
  "node_type": "DATA_INPUT",
  "dependencies": {
    "request": {
      "node": "input_node",
      "output": null,
      "key": null,
      "hierarchy": null
    }
  },
  "metadata": {
    "data_source": "customer_database",
    "parameters": {
      "table": "customers",
      "filter_by": "tax_id",
      "filter_value": "{{request.tax_id}}"
    }
  }
}
```

### INPUT

Defines the input schema for the workflow (automatically created by the system).

**Metadata Properties:**
```json
{
  "schema": {
    "param_name": "type"    // Parameter definitions
  }
}
```

**Note:** INPUT nodes are typically auto-generated and don't need to be manually created.

## Input Schema

The input schema defines the expected parameters for workflow execution:

```json
{
  "input_schema": {
    "tax_id": "str",
    "amount": "float",
    "product_type": "str",
    "customer_age": "int"
  }
}
```

Supported types:
- `"str"`: String values
- `"int"`: Integer values  
- `"float"`: Floating-point numbers
- `"bool"`: Boolean values
- `"dict"`: Dictionary objects
- `"list"`: Array values

## Template Expressions

Within node metadata, you can use template expressions to reference data from other nodes:

- `{{inputs.parameter_name}}`: Reference input parameters
- `{{node_name.field}}`: Reference output from another node
- `{{config.variable_name}}`: Reference configuration variables

## Complete Example

Here's a complete workflow specification for a credit approval process:

```json
{
  "nodes": [
    {
      "name": "credit_api",
      "node_type": "CONNECTION",
      "dependencies": {
        "inputs": {
          "node": "input_node",
          "output": null,
          "key": null,
          "hierarchy": null
        }
      },
      "metadata": {
        "url": "https://api.creditbureau.com/check",
        "method": "POST",
        "headers": {
          "Authorization": "Bearer {{config.api_key}}",
          "Content-Type": "application/json"
        },
        "body": {
          "tax_id": "{{inputs.tax_id}}",
          "amount": "{{inputs.loan_amount}}"
        },
        "timeout": 30,
        "retry_max_retries": 2,
        "response_type": "JSON"
      }
    },
    {
      "name": "risk_decision",
      "node_type": "DECISION",
      "dependencies": {
        "credit_data": {
          "node": "credit_api",
          "output": null,
          "key": null,
          "hierarchy": null
        }
      },
      "metadata": {
        "conditions": [
          {
            "decision_type": "if",
            "condition": "credit_data.score > 750 and credit_data.debt_ratio < 0.3",
            "output": "approved"
          },
          {
            "decision_type": "else-if",
            "condition": "credit_data.score > 600",
            "output": "manual_review"
          },
          {
            "decision_type": "else",
            "condition": null,
            "output": "denied"
          }
        ]
      }
    },
    {
      "name": "approved",
      "node_type": "TERMINATE",
      "dependencies": {
        "condition": {
          "node": "risk_decision",
          "output": "approved",
          "key": null,
          "hierarchy": null
        }
      },
      "metadata": {
        "return_status": "approved",
        "return_metadata": {
          "input_data": {
            "node": "input_node",
            "output": null,
            "key": null,
            "hierarchy": null
          },
          "credit_report": {
            "node": "credit_api",
            "output": null,
            "key": null,
            "hierarchy": null
          }
        }
      }
    },
    {
      "name": "manual_review",
      "node_type": "TERMINATE",
      "dependencies": {
        "condition": {
          "node": "risk_decision",
          "output": "manual_review",
          "key": null,
          "hierarchy": null
        }
      },
      "metadata": {
        "return_status": "manual_review",
        "return_metadata": {
          "input_data": {
            "node": "input_node",
            "output": null,
            "key": null,
            "hierarchy": null
          },
          "credit_report": {
            "node": "credit_api",
            "output": null,
            "key": null,
            "hierarchy": null
          }
        }
      }
    },
    {
      "name": "denied",
      "node_type": "TERMINATE",
      "dependencies": {
        "condition": {
          "node": "risk_decision",
          "output": "denied",
          "key": null,
          "hierarchy": null
        }
      },
      "metadata": {
        "return_status": "denied",
        "return_metadata": {
          "input_data": {
            "node": "input_node",
            "output": null,
            "key": null,
            "hierarchy": null
          }
        }
      }
    }
  ],
  "input_schema": {
    "tax_id": "str",
    "loan_amount": "float"
  },
  "config_variables": ["api_key"]
}
```

## Best Practices

### Node Naming
- Use descriptive, lowercase names with underscores
- Avoid spaces and special characters
- Keep names concise but meaningful

### Workflow Design
- Always end execution paths with TERMINATE nodes
- Use DECISION nodes for conditional logic
- Keep transform functions simple and focused
- Document complex logic in node descriptions

### Error Handling
- Set appropriate timeouts for CONNECTION nodes
- Configure retry logic for external API calls
- Use DECISION nodes to handle error conditions

### Performance
- Minimize the number of external API calls
- Use DATA_INPUT nodes for efficient data fetching
- Consider caching strategies for frequently accessed data

## Validation Rules

1. **Required Fields**: All nodes must have `name`, `node_type`, and appropriate `metadata`
2. **Unique Names**: Node names must be unique within the workflow
3. **Valid Dependencies**: All dependency references must point to existing nodes
4. **Terminate Nodes**: All execution paths must end with TERMINATE nodes
5. **Decision Logic**: DECISION nodes must have both `if` and `else` conditions
6. **Input Schema**: Must define all parameters referenced in the workflow

This specification provides a complete reference for creating Vulkan workflow JSON definitions that can be processed by the core engine, regardless of how they were originally created (Python client, web UI, or AI copilot).
