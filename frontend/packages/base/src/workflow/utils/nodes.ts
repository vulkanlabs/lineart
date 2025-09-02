import type { XYPosition } from "@xyflow/react";
import type { VulkanNodeType, VulkanNode, NodeConfig } from "../types/workflow";
import { standardizeNodeName } from "./names";

/**
 * Default node size constants
 */
export const NODE_SIZE = { width: 320, height: 50 };

/**
 * Configuration for each node type including dimensions and associated icons
 */
export const nodesConfig: Record<VulkanNodeType, NodeConfig> = {
    INPUT: {
        id: "INPUT",
        name: "input_node",
        width: 450,
        height: 225,
        icon: "INPUT",
    },
    DECISION: {
        id: "DECISION",
        name: "Decision Node",
        width: 400,
        height: 308,
        icon: "BRANCH",
    },
    BRANCH: {
        id: "BRANCH",
        name: "Branch Node",
        width: 450,
        height: 500,
        icon: "BRANCH",
    },
    TERMINATE: {
        id: "TERMINATE",
        name: "Terminate Node",
        width: 450,
        height: 400,
        icon: "TERMINATE",
    },
    CONNECTION: {
        id: "CONNECTION",
        name: "Connection Node",
        width: 450,
        height: 225,
        icon: "CONNECTION",
    },
    DATA_INPUT: {
        id: "DATA_INPUT",
        name: "Data Input Node",
        width: 450,
        height: 225,
        icon: "DATA_INPUT",
    },
    TRANSFORM: {
        id: "TRANSFORM",
        name: "Transform Node",
        width: 450,
        height: 300,
        icon: "TRANSFORM",
    },
    POLICY: {
        id: "POLICY",
        name: "Policy Node",
        width: 400,
        height: 200,
        icon: "POLICY",
    },
    COMPONENT: {
        id: "COMPONENT",
        name: "Component Node",
        width: 450,
        height: 400,
        icon: "COMPONENT",
    },
};

/**
 * Initialize default metadata for each node type
 * @param {VulkanNodeType} type - The type of node being created
 * @returns {Object} Default metadata object for the node type
 *
 * Each node type needs different default config
 * Examples: TERMINATE needs return_status, BRANCH needs choices array
 */
function initMetadata(type: VulkanNodeType) {
    switch (type) {
        case "TERMINATE":
            return {
                return_status: "",
            };
        case "TRANSFORM":
            return {
                source_code: "",
            };
        case "BRANCH":
            return {
                source_code: "",
                choices: ["", ""],
            };
        case "INPUT":
            return {
                schema: {},
            };
        case "CONNECTION":
            return {
                url: "",
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                },
                params: {},
                body: {},
                timeout: 30,
                retry_max_retries: 1,
                response_type: "JSON",
            };
        case "DECISION":
            return {
                conditions: [
                    { decision_type: "if" as const, condition: "", output: "condition_1" },
                    { decision_type: "else" as const, output: "condition_2" },
                ],
            };
        case "DATA_INPUT":
            return {
                data_source: "",
            };
        case "POLICY":
            return {
                policy_id: "",
            };
        default:
            return {};
    }
}

/**
 * Create a new workflow node with proper initialization and unique naming
 * @param {Object} params - Node creation parameters
 * @param {VulkanNodeType} params.type - Type of node to create (INPUT, DECISION, etc.)
 * @param {XYPosition} [params.position={x:0,y:0}] - Where to place the node on canvas
 * @param {VulkanNode[]} [params.existingNodes=[]] - Existing nodes for unique name generation
 * @returns {VulkanNode|null} Created node or null if invalid type
 *
 * Naming: "decision_node_1", "decision_node_2" etc. based on existing nodes
 * Example: createNodeByType({ type: "DECISION", position: {x: 100, y: 200}, existingNodes })
 */
export function createNodeByType({
    type,
    position = { x: 0, y: 0 },
    existingNodes = [],
}: {
    type: VulkanNodeType;
    position?: XYPosition;
    existingNodes: VulkanNode[];
}): VulkanNode | null {
    const nodeConfig = nodesConfig[type];
    if (!nodeConfig) {
        console.error(`Unknown node type: ${type}`);
        return null;
    }

    const width = nodeConfig.width ?? NODE_SIZE.width;
    const height = nodeConfig.height ?? NODE_SIZE.height;
    const metadata = initMetadata(type);

    // For INPUT node, use a fixed ID and return directly
    if (type === "INPUT") {
        return {
            id: "input_node",
            data: {
                name: "input_node",
                minWidth: width,
                minHeight: height,
                icon: nodeConfig.icon,
                metadata: metadata,
                incomingEdges: {},
                detailsExpanded: true,
            },
            position: {
                x: position.x,
                y: position.y - height * 0.5,
            },
            width: width,
            height: height,
            type,
        };
    }

    // For all other node types, generate a unique name and create the node
    const sameTypeNodes = existingNodes.filter((n) => n.type === type);
    const nextNumber = sameTypeNodes.length + 1;
    const uniqueName = standardizeNodeName(`${nodeConfig.name} ${nextNumber}`);

    const newNode: VulkanNode = {
        id: uniqueName,
        data: {
            name: uniqueName,
            minWidth: width,
            minHeight: height,
            icon: nodeConfig.icon,
            metadata: metadata,
            incomingEdges: {},
            detailsExpanded: true,
        },
        position: {
            x: position.x,
            y: position.y - height * 0.5,
        },
        width: width,
        height: height,
        type,
    };

    return newNode;
}
