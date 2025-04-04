import { XYPosition } from "@xyflow/react";
import { nanoid } from "nanoid";

import { VulkanNodeType, VulkanNode, NodeConfig } from "./types";

export const NODE_SIZE = { width: 320, height: 50 };

export const nodesConfig: Record<VulkanNodeType, NodeConfig> = {
    "INPUT": {
        id: "INPUT",
        name: "InputNode",
        width: 260,
        height: 50,
        icon: null,
    },
    "CONNECTION": {
        id: "CONNECTION",
        name: "ConnectionNode",
        icon: "Link",
    },
    "DATA_INPUT": {
        id: "DATA_INPUT",
        name: "DataSourceNode",
        icon: "ArrowDown01",
    },
    "TRANSFORM": {
        id: "TRANSFORM",
        name: "TransformNode",
        width: 400,
        height: 300,
        icon: "Code2",
    },
    "BRANCH": {
        id: "BRANCH",
        name: "BranchNode",
        width: 500,
        height: 500,
        icon: "Split",
    },
    "TERMINATE": {
        id: "TERMINATE",
        name: "TerminateNode",
        width: 400,
        height: 200,
        icon: "ArrowRightFromLine",
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
        };
    } else if (type === "BRANCH") {
        return {
            func: null,
            source_code: "",
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
