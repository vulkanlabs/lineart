import { Node, NodeProps, XYPosition } from "@xyflow/react";
import { nanoid } from "nanoid";

import { NODE_SIZE } from "./base";

export type WorkflowNodeData = {
    title?: string;
    label?: string;
    // icon?: keyof typeof iconMapping;
    icon?: string;
    minHeight?: number;
    minWidth?: number;
    metadata?: any;
};

export type NodeConfig = {
    id: string;
    title: string;
    icon: string;
    height?: number;
    width?: number;
};

export const nodesConfig: Record<VulkanNodeType, NodeConfig> = {
    "input-node": {
        id: "input-node",
        title: "Input Node",
        icon: null,
    },
    "connection-node": {
        id: "connection-node",
        title: "Connection Node",
        icon: "Link",
    },
    "data-source-node": {
        id: "data-source-node",
        title: "Data Source Node",
        icon: "ArrowDown01",
    },
    "transform-node": {
        id: "transform-node",
        title: "Transform Node",
        height: 300,
        width: 600,
        icon: "Code2",
    },
    "branch-node": {
        id: "branch-node",
        title: "Branch Node",
        icon: "Split",
    },
    "terminate-node": {
        id: "terminate-node",
        title: "Terminate Node",
        height: 200,
        width: 400,
        icon: "ArrowRightFromLine",
    },
};

export function createNodeByType({
    type,
    id,
    position = { x: 0, y: 0 },
    data,
}: {
    type: VulkanNodeType;
    id?: string;
    position?: XYPosition;
    data?: WorkflowNodeData;
}): VulkanNode {
    const node = nodesConfig[type];

    const newNode: VulkanNode = {
        id: id ?? nanoid(),
        data: data ?? {
            title: node.title,
            // status: node.status,
            minHeight: node.height,
            minWidth: node.width,
            icon: node.icon,
        },
        position: {
            x: position.x - NODE_SIZE.width * 0.5,
            y: position.y - NODE_SIZE.height * 0.5,
        },
        height: node.height ?? NODE_SIZE.height,
        width: node.width ?? NODE_SIZE.width,
        type,
    };

    return newNode;
}

export type VulkanNode =
    | Node<WorkflowNodeData, "input-node">
    | Node<WorkflowNodeData, "connection-node">
    | Node<WorkflowNodeData, "data-source-node">
    | Node<WorkflowNodeData, "transform-node">
    | Node<WorkflowNodeData, "branch-node">
    | Node<WorkflowNodeData, "terminate-node">;

export type VulkanNodeType = NonNullable<VulkanNode["type"]>;
