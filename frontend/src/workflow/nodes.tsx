import { XYPosition } from "@xyflow/react";

import { VulkanNodeType, VulkanNode, NodeConfig } from "./types";
import { standardizeNodeName } from "./names";

export const NODE_SIZE = { width: 320, height: 50 };

export const nodesConfig: Record<VulkanNodeType, NodeConfig> = {
    INPUT: {
        id: "INPUT",
        name: "input_node",
        width: 260,
        height: 50,
        icon: null,
    },
    CONNECTION: {
        id: "CONNECTION",
        name: "Connection Node",
        icon: "CONNECTION",
    },
    DATA_INPUT: {
        id: "DATA_INPUT",
        name: "Data Input Node",
        width: 400,
        height: 225,
        icon: "DATA_INPUT",
    },
    TRANSFORM: {
        id: "TRANSFORM",
        name: "Transform Node",
        width: 400,
        height: 300,
        icon: "TRANSFORM",
    },
    BRANCH: {
        id: "BRANCH",
        name: "Branch Node",
        width: 500,
        height: 500,
        icon: "BRANCH",
    },
    TERMINATE: {
        id: "TERMINATE",
        name: "Terminate Node",
        width: 400,
        height: 400,
        icon: "TERMINATE",
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

    // For INPUT node, use a fixed ID
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

    // Find all existing nodes of this type and create the new name
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
