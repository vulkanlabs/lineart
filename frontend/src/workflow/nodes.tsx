import { XYPosition } from "@xyflow/react";
import { nanoid } from "nanoid";

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
        width: 400,
        height: 200,
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
}: {
    type: VulkanNodeType;
    position?: XYPosition;
}): VulkanNode {
    const node = nodesConfig[type];
    const width = node.width ?? NODE_SIZE.width;
    const height = node.height ?? NODE_SIZE.height;
    const metadata = initMetadata(type);

    const newNode: VulkanNode = {
        id: nanoid(),
        data: {
            name: node.name,
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
