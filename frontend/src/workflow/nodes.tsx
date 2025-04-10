import { XYPosition } from "@xyflow/react";

import { VulkanNodeType, VulkanNode, NodeConfig } from "./types";

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
        height: 200,
        icon: "TERMINATE",
    },
};

function initMetadata(type: VulkanNodeType) {
    if (type === "TERMINATE") {
        return {
            return_status: "",
        };
    } else if (type === "TRANSFORM") {
        return {
            func: null,
            source_code: "",
            function_code: "",
        };
    } else if (type === "BRANCH") {
        return {
            func: null,
            source_code: "",
            function_code: "",
            choices: ["", ""],
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
    const uniqueName = `${node.name} ${nextNumber}`;

    const newNode: VulkanNode = {
        id: standardizeNodeName(uniqueName),
        data: {
            name: uniqueName,
            minWidth: width,
            minHeight: height,
            icon: node.icon,
            metadata: metadata,
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

export function standardizeNodeName(name: string): string {
    return name.replace(/\s+/g, "_").toLowerCase();
}
