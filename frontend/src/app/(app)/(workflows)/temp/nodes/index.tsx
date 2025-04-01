import { Node, NodeProps, XYPosition } from "@xyflow/react";
import { nanoid } from "nanoid";

// import { NODE_SIZE } from "./base";
export const NODE_SIZE = { width: 320, height: 50 };

export type WorkflowNodeData = {
    name?: string;
    // icon?: keyof typeof iconMapping;
    icon?: string;
    minHeight?: number;
    minWidth?: number;
    metadata?: any;
};

export type NodeConfig = {
    id: string;
    name: string;
    icon: string;
    height?: number;
    width?: number;
};

export const nodesConfig: Record<VulkanNodeType, NodeConfig> = {
    "input-node": {
        id: "input-node",
        name: "Input Node",
        width: 260,
        height: 50,
        icon: null,
    },
    "connection-node": {
        id: "connection-node",
        name: "Connection Node",
        icon: "Link",
    },
    "data-source-node": {
        id: "data-source-node",
        name: "Data Source Node",
        icon: "ArrowDown01",
    },
    "transform-node": {
        id: "transform-node",
        name: "Transform Node",
        width: 400,
        height: 300,
        icon: "Code2",
    },
    "branch-node": {
        id: "branch-node",
        name: "Branch Node",
        width: 500,
        height: 500,
        icon: "Split",
    },
    "terminate-node": {
        id: "terminate-node",
        name: "Terminate Node",
        width: 400,
        height: 200,
        icon: "ArrowRightFromLine",
    },
};

export type NodeDependency = {
    node: string;
    output?: string | null;
    key?: string | null;
};

export type GenericNodeDefinition<MetadataType> = {
    name: string;
    node_type: string;
    // description: string;
    metadata?: MetadataType;
    dependencies?: NodeDependency[];
};

export type TerminateNodeMetadata = {
    returnStatus: string;
};

export type TransformNodeMetadata = {
    sourceCode: string;
};

export type BranchNodeMetadata = {
    sourceCode: string;
    choices: string[];
};

export type NodeDefinition = GenericNodeDefinition<
    TerminateNodeMetadata | TransformNodeMetadata | BranchNodeMetadata
>;

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
    const width = node.width ?? NODE_SIZE.width;
    const height = node.height ?? NODE_SIZE.height;
    const metadata = initMetadata(type);

    const newNode: VulkanNode = {
        id: id ?? nanoid(),
        data: data ?? {
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

export type VulkanNode =
    | Node<WorkflowNodeData, "input-node">
    | Node<WorkflowNodeData, "connection-node">
    | Node<WorkflowNodeData, "data-source-node">
    | Node<WorkflowNodeData, "transform-node">
    | Node<WorkflowNodeData, "branch-node">
    | Node<WorkflowNodeData, "terminate-node">;

export type VulkanNodeType = NonNullable<VulkanNode["type"]>;
