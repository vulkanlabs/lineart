"use client";

import { useMemo } from "react";
import { PolicyVersion } from "@vulkan-server/PolicyVersion";
import { WorkflowProvider } from "@/workflow/store";
import { WorkflowContextManager } from "./workflow-context-manager";
import WorkflowFrame from "@/workflow/workflow";
import { VulkanNode, WorkflowState } from "@/workflow/types";
import { nodesConfig } from "@/workflow/nodes";
import { iconMapping } from "@/workflow/icons";
import { XYPosition } from "@xyflow/react";

interface WorkflowPageWrapperProps {
    policyVersion: PolicyVersion;
}

function makeInputNode(inputSchema: { [key: string]: string }, inputNodeUIMetadata: any) {
    // This is a simplified version - we should extract this logic from WorkflowFrame
    // For now, create a basic input node
    return {
        id: "input",
        type: "INPUT" as const,
        position: inputNodeUIMetadata?.position || { x: 100, y: 100 },
        data: {
            name: "input",
            icon: "INPUT",
            metadata: { schema: inputSchema },
            incomingEdges: {},
        },
        height: inputNodeUIMetadata?.height || 200,
        width: inputNodeUIMetadata?.width || 300,
    };
}

function getDefaultUIMetadata(nodeType: string) {
    const nodeConfig = nodesConfig[nodeType];
    return {
        position: { x: 0, y: 0 },
        width: nodeConfig?.width || 200,
        height: nodeConfig?.height || 100,
    };
}

export function WorkflowPageWrapper({ policyVersion }: WorkflowPageWrapperProps) {
    const initialState: WorkflowState = useMemo(() => {
        const uiMetadata = policyVersion.ui_metadata || {};
        const inputNode = makeInputNode(policyVersion.input_schema, uiMetadata["input_node"]);

        // If no spec is defined, return an empty state: new version
        if (!policyVersion.spec || policyVersion.spec.nodes.length === 0) {
            return defaultWorkflowState(inputNode);
        }

        const nodes = policyVersion.spec.nodes || [];
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
                    const [key, dependency] = Object.entries(node.dependencies).find(
                        ([, dep]) => dep.node === edge.source,
                    );
                    acc[edge.id] = { key, dependency };
                    return acc;
                }, {});

            const nodeType = node.node_type as keyof typeof iconMapping;
            return {
                id: node.name,
                type: nodeType,
                height: height,
                width: width,
                data: {
                    name: node.name,
                    icon: nodeType,
                    metadata: node.metadata || {},
                    incomingEdges: incomingEdges,
                },
                position,
            };
        });

        // Add the input node to the flow nodes
        const allNodes = [inputNode, ...flowNodes];

        return {
            nodes: allNodes,
            edges: edges,
        };
    }, [policyVersion]);

    return (
        <WorkflowProvider initialState={initialState}>
            <WorkflowContextManager policyVersion={policyVersion} />
            <WorkflowFrame policyVersion={policyVersion} />
        </WorkflowProvider>
    );
}
