import { XYPosition } from "@xyflow/react";

import { VulkanNodeType, VulkanNode, NodeConfig } from "./types";
import { standardizeNodeName } from "./names";

export const NODE_SIZE = { width: 320, height: 50 };

export const nodesConfig: Record<VulkanNodeType, NodeConfig> = {
    INPUT: {
        id: "INPUT",
        name: "input_node",
        width: 450,
        height: 225,
        icon: null,
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
};

function initMetadata(type: VulkanNodeType) {
    if (type === "TERMINATE") {
        return {
            return_status: "",
        };
    } else if (type === "TRANSFORM") {
        return {
            source_code: "",
        };
    } else if (type === "BRANCH") {
        return {
            source_code: "",
            choices: ["", ""],
        };
    } else if (type === "INPUT") {
        return {
            schema: {},
        };
    } else if (type === "CONNECTION") {
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
    } else if (type === "DECISION") {
        return {
            conditions: [
                { decision_type: "if", condition: "", output: "condition_1" },
                { decision_type: "else", output: "condition_2" },
            ],
        };
    }

    return {};
}

export function createNodeByType({
    type,
    position = { x: 0, y: 0 },
    existingNodes = [],
}: {
    type: VulkanNodeType;
    position?: XYPosition;
    existingNodes: VulkanNode[];
}): VulkanNode {
    const node = nodesConfig[type];
    const width = node.width ?? NODE_SIZE.width;
    const height = node.height ?? NODE_SIZE.height;
    const metadata = initMetadata(type);

    // For INPUT node, use a fixed ID and return directly
    if (type === "INPUT") {
        return {
            id: "input_node",
            data: {
                name: "input_node",
                minWidth: width,
                minHeight: height,
                icon: node.icon,
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

    // For all other node types (including DECISION), generate a unique name and create the node
    const sameTypeNodes = existingNodes.filter((n) => n.type === type);
    const nextNumber = sameTypeNodes.length + 1;
    const uniqueName = standardizeNodeName(`${node.name} ${nextNumber}`);

    const newNode: VulkanNode = {
        id: uniqueName,
        data: {
            name: uniqueName,
            minWidth: width,
            minHeight: height,
            icon: node.icon,
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
