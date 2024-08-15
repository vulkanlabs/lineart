"use client";

import React, { useState, useLayoutEffect, useCallback } from "react";
import {
    ReactFlow,
    ReactFlowProvider,
    MiniMap,
    Controls,
    ConnectionLineType,
    Background,
    BackgroundVariant,
    useNodesState,
    useEdgesState,
    useReactFlow,
} from '@xyflow/react';

import ELK from 'elkjs/lib/elk.bundled.js';

import '@xyflow/react/dist/style.css';


function LayoutFlow({ policyId, onNodeClick }) {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const { fitView } = useReactFlow();

    const elk = new ELK();

    const elkOptions = {
        'elk.algorithm': 'layered',
        'elk.layered.spacing.nodeNodeBetweenLayers': '50',
        'elk.spacing.nodeNode': '80',
        'elk.direction': 'DOWN',
    };

    const onLayout = useCallback(
        () => {
            assembleGraph(policyId, elk, elkOptions)
                .then(([layoutedNodes, layoutedEdges]) => {
                    console.log("nodes:", layoutedNodes);
                    console.log("edges:", layoutedEdges);

                    setNodes(layoutedNodes);
                    setEdges(layoutedEdges);

                    window.requestAnimationFrame(() => fitView());
                });
        },
        [nodes, edges],
    );

    // Calculate the initial layout on mount.
    useLayoutEffect(() => {
        onLayout();
    }, []);

    return (
        <ReactFlowProvider>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeClick={onNodeClick}
                connectionLineType={ConnectionLineType.SmoothStep}
                fitView
            >
                <Background color="#ccc" variant={BackgroundVariant.Dots} />
                <MiniMap nodeStrokeWidth={3} zoomable pannable />
                <Controls />
            </ReactFlow>
        </ReactFlowProvider>
    );
}

export default ({ policyId, onNodeClick }) => (
    <ReactFlowProvider>
        <LayoutFlow policyId={policyId} onNodeClick={onNodeClick} />
    </ReactFlowProvider>
);


async function assembleGraph(policyId, elk, options) {
    const graphData = await getPolicyVersionData(policyId)
        .then((policyVersionData) => {
            return JSON.parse(policyVersionData.graph_definition);
        });

    function makeNodes(node, options, parent = null) {
        const nodeWidth = 172;
        const nodeHeight = 36;

        let nodeConfig = {
            id: node.name,
            data: {
                label: node.name,
                description: node.description,
                type: node.node_type,
                dependencies: node.dependencies,
            },
            // Adjust the target and source handle positions based on the layout
            // direction.
            targetPosition: 'top',
            sourcePosition: 'bottom',

            // Hardcode a width and height for elk to use when layouting.
            width: nodeWidth,
            height: nodeHeight,
        };

        if (parent) {
            nodeConfig.parentId = parent;
            // nodeConfig.style = { backgroundColor: 'rgba(240,240,240,0.25)' }
        }

        if (node.node_type === 'COMPONENT') {
            nodeConfig.children = Object.values(node.metadata.nodes).map(
                (n) => makeNodes(n, options, node.name)
            );
            nodeConfig.layoutOptions = options;
            nodeConfig.type = "group";
            return nodeConfig;
        }

        if (node.metadata !== null) {
            Object.entries(node.metadata).map(([key, value]) => {
                nodeConfig.data[key] = value;
            })
        }

        return nodeConfig;
    }

    function makeEdges(node, nodesMap) {
        if (node.dependencies === null) {
            return [];
        }

        function __makeEdges(node, elk_specific = false) {
            return node.dependencies.flatMap((dep) => {
                // TODO: If `dep` is an array, it means that it comes from
                // a specific output of a node. For now, we discard it, as
                // we don't display the node outputs.
                if (Array.isArray(dep)) {
                    dep = dep[0];
                }

                const edge = {
                    id: `${dep}-${node.name}`,
                    source: dep,
                    target: node.name,
                    elk_specific: elk_specific,
                };

                // In order for Elk to layout the edges correctly when the
                // dependency is the output of a Component, we need to add
                // an edge between the Component and the target node.
                const depNode = nodesMap[dep];

                if (depNode?.parentId && nodesMap[node.name]?.parentId != depNode.parentId) {
                    const parentEdge = {
                        id: `${depNode.parentId}-${node.name}`,
                        source: depNode.parentId,
                        target: node.name,
                        elk_specific: true,
                    };
                    return [edge, parentEdge];
                }

                return edge;
            });
        }

        if (node.node_type == "COMPONENT") {
            const innerNodes = Object.values(node.metadata.nodes);
            const innerEdges = innerNodes.flatMap((n) => makeEdges(n, nodesMap));
            return [...__makeEdges(node, true), ...innerEdges];
        }

        return __makeEdges(node);
    }

    function flattenNodes(node) {
        if (node?.children) {
            const flattenedNodes = node.children.flatMap((n) => flattenNodes(n));
            return [{ [node.id]: node }, ...flattenedNodes];
        }
        return { [node.id]: node };
    }

    const rawNodes = Object.values(graphData);
    const structuredNodes = rawNodes.map((node) => makeNodes(node, options));

    const flattenedNodes = structuredNodes.flatMap((n) => flattenNodes(n));
    const nodesMap = Object.assign({}, ...flattenedNodes);

    const edges = rawNodes.flatMap((node) => makeEdges(node, nodesMap));

    const [layoutedNodes, layoutedEdges] = await getLayoutedElements(
        structuredNodes, edges, elk, options
    );

    // Filter out the edges that are specific to Elk (otherwise ReactFlow will
    // raise several warnings).
    const filteredEdges = layoutedEdges.filter((edge) => !edge.elk_specific);

    return [layoutedNodes, filteredEdges];
}


function getLayoutedElements(nodes, edges, elk, options) {
    const graph = {
        id: 'root',
        layoutOptions: options,
        children: [{ id: 'all', layoutOptions: options, children: nodes }],
        edges: edges,
    };

    return elk
        .layout(graph)
        .then((layoutedGraph) => {
            console.log(layoutedGraph);

            const _format_node = (node) => ({
                ...node,
                // React Flow expects a position property on the node instead of `x`
                // and `y` fields.
                position: { x: node.x, y: node.y },
            });

            const extractChildren = (node) => {
                if (node.children) {
                    const children = node.children.flatMap((child) => extractChildren(child));
                    return [_format_node(node), ...children];
                }
                return _format_node(node);
            }

            let _nodes = layoutedGraph.children.flatMap((node) => extractChildren(node));
            _nodes = _nodes.filter((node) => node.id !== 'all');

            return [_nodes, edges];
        })
        .catch(console.error);
};


async function getPolicyVersionData(policyId) {
    const baseUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    const policyUrl = new URL(`/policies/${policyId}`, baseUrl);
    const policyVersionId = await fetch(policyUrl)
        .then((res) => res.json())
        .catch((error) => {
            throw new Error("Failed to fetch policy version id for policy",
                { cause: error });
        })
        .then((response) => {
            if (response.active_policy_version_id === null) {
                throw new Error(`Policy ${policyId} has no active version`);
            }
            return response.active_policy_version_id;
        });


    if (policyVersionId === null) {
        throw new Error(`Policy ${policyId} has no active version`);
    }

    const versionUrl = new URL(`/policyVersions/${policyVersionId}`, baseUrl);
    const data = await fetch(versionUrl)
        .then((res) => res.json())
        .catch((error) => {
            throw new Error("Failed to fetch graph data", { cause: error });
        });
    return data;
}