import type { XYPosition, Edge } from "@xyflow/react";
import type { NodeDefinitionDict, UIMetadata } from "@vulkanlabs/client-open";

import { createNodeByType, nodesConfig } from "./nodes";
import { findHandleIndexByName } from "./names";
import type { VulkanNode, WorkflowState } from "../types/workflow";
import { Workflow } from "../api/types";

/**
 * Create initial workflow state from a policy version
 */
export function createWorkflowState(workflow: Workflow): WorkflowState {
    const uiMetadata = workflow.workflow?.ui_metadata || {};
    const inputNode = makeInputNode(
        workflow.workflow?.spec.input_schema || {},
        uiMetadata["input_node"],
    );

    // If no spec is defined, return an empty state: new version
    if (
        !workflow.workflow?.spec ||
        !workflow.workflow?.spec.nodes ||
        workflow.workflow?.spec.nodes.length === 0
    ) {
        return defaultWorkflowState(inputNode);
    }

    const nodes = workflow.workflow?.spec.nodes || [];
    const edges = makeEdgesFromDependencies(nodes);

    // Map server nodes to ReactFlow node format
    const flowNodes: VulkanNode[] = nodes.map((node) => {
        const nodeUIMetadata = uiMetadata[node.name] || getDefaultUIMetadata(node.node_type);
        const position: XYPosition = nodeUIMetadata.position;
        const height = nodeUIMetadata.height;
        const width = nodeUIMetadata.width;

        const incomingEdges = edges
            .filter((edge) => edge.target === node.name)
            .reduce((acc: any, edge: any) => {
                const dependencyEntry = Object.entries(node.dependencies || {}).find(
                    ([, dep]) => dep.node === edge.source,
                );
                if (dependencyEntry) {
                    const [key, dependency] = dependencyEntry;
                    acc[edge.id] = { key, dependency };
                }
                return acc;
            }, {});

        return {
            id: node.name,
            type: node.node_type as any,
            height: height,
            width: width,
            data: {
                name: node.name,
                icon: node.node_type,
                metadata: node.metadata || {},
                incomingEdges: incomingEdges,
                minWidth: width,
                minHeight: height,
                detailsExpanded: true,
            },
            position: position,
        };
    });

    return {
        nodes: [inputNode, ...flowNodes],
        edges: edges,
        autoSave: {
            lastSaved: null,
            isSaving: false,
            hasUnsavedChanges: false,
            saveError: null,
            autoSaveEnabled: true,
            retryCount: 0,
        },
        sidebar: {
            isOpen: false,
            selectedNodeId: null,
            activeTab: null,
        },
    };
}

/**
 * Create input node with proper metadata
 */
function makeInputNode(
    inputSchema: { [key: string]: string },
    inputNodeUIMetadata?: UIMetadata,
): VulkanNode {
    // Create the input node with proper metadata if available
    let inputNode = defaultInputNode;
    if (inputNodeUIMetadata) {
        inputNode = {
            ...inputNode,
            position: inputNodeUIMetadata?.position || inputNode.position,
            width: inputNodeUIMetadata?.width || inputNode.width,
        };
    }
    if (inputSchema) {
        inputNode = {
            ...inputNode,
            data: {
                ...inputNode.data,
                metadata: {
                    ...inputNode.data.metadata,
                    schema: inputSchema,
                },
            },
        };
    }
    return inputNode;
}

/**
 * Default input node
 */
const defaultInputNode = createNodeByType({
    type: "INPUT",
    position: { x: 200, y: 200 },
    existingNodes: [],
})!;

/**
 * Default workflow state with just the input node
 */
function defaultWorkflowState(inputNode: VulkanNode): WorkflowState {
    return {
        nodes: [inputNode],
        edges: [],
        autoSave: {
            lastSaved: null,
            isSaving: false,
            hasUnsavedChanges: false,
            saveError: null,
            autoSaveEnabled: true,
            retryCount: 0,
        },
        sidebar: {
            isOpen: false,
            selectedNodeId: null,
            activeTab: null,
        },
    };
}

/**
 * Get default UI metadata for a node type
 */
function getDefaultUIMetadata(nodeType: string) {
    const nodeConfig = nodesConfig[nodeType as keyof typeof nodesConfig];
    return {
        position: { x: 0, y: 0 },
        width: nodeConfig?.width || 320,
        height: nodeConfig?.height || 200,
    };
}

/**
 * Create edges from node dependencies
 */
function makeEdgesFromDependencies(nodes: NodeDefinitionDict[]): Edge[] {
    // Return early if nodes array is empty or invalid
    if (!nodes || nodes.length === 0) {
        return [];
    }

    const allNodes: NodeDefinitionDict[] = [
        ...nodes,
        { name: "input_node", node_type: "INPUT" } as NodeDefinitionDict,
    ];
    const edgeList: Edge[] = [];

    // Process each node's dependencies
    allNodes.forEach((node) => {
        // Skip if node has no dependencies
        if (!node.dependencies) {
            return;
        }

        const target = node.name;
        const targetHandle = null;

        Object.entries(node.dependencies).forEach(([_, dep]) => {
            const source = dep.node;
            let sourceHandle: string | null = null;

            // If the output is specified, we need to find the corresponding
            // handle index in the node.
            if (dep.output) {
                const sourceNode = nodes.find((n) => n.name === dep.node);
                if (!sourceNode) {
                    console.error(`Node ${dep.node} not found`);
                    return;
                }

                const handleIndex = findHandleIndexByName(sourceNode, dep.output);
                if (handleIndex === null) {
                    console.error(`Output ${dep.output} not found in node ${dep.node}`);
                    return;
                }
                sourceHandle = handleIndex.toString();
            }

            // Skip if source is the same as target
            if (source === target) {
                return;
            }

            // Create edge object
            const edge: Edge = {
                id: `${source}-${target}`,
                source: source,
                target: target,
                sourceHandle: sourceHandle,
                targetHandle: targetHandle,
                type: "default",
            };

            // Add edge to the list
            edgeList.push(edge);
        });
    });

    return edgeList;
}
