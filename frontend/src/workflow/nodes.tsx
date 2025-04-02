import { XYPosition } from "@xyflow/react";
import { nanoid } from "nanoid";

import { VulkanNodeType, VulkanNode, NodeConfig } from "./types";

export const NODE_SIZE = { width: 320, height: 50 };

export const nodesConfig: Record<VulkanNodeType, NodeConfig> = {
    "input-node": {
        id: "input-node",
        name: "InputNode",
        width: 260,
        height: 50,
        icon: null,
    },
    "connection-node": {
        id: "connection-node",
        name: "ConnectionNode",
        icon: "Link",
    },
    "data-source-node": {
        id: "data-source-node",
        name: "DataSourceNode",
        icon: "ArrowDown01",
    },
    "transform-node": {
        id: "transform-node",
        name: "TransformNode",
        width: 400,
        height: 300,
        icon: "Code2",
    },
    "branch-node": {
        id: "branch-node",
        name: "BranchNode",
        width: 500,
        height: 500,
        icon: "Split",
    },
    "terminate-node": {
        id: "terminate-node",
        name: "TerminateNode",
        width: 400,
        height: 200,
        icon: "ArrowRightFromLine",
    },
};

function initMetadata(type: VulkanNodeType) {
    if (type === "terminate-node") {
        return {
            returnStatus: "",
        };
    } else if (type === "transform-node") {
        return {
            sourceCode: "",
        };
    } else if (type === "branch-node") {
        return {
            sourceCode: "",
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
            x: position.x - width * 0.5,
            y: position.y - height * 0.5,
        },
        width: width,
        height: height,
        type,
    };

    return newNode;
}
