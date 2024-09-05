"use client";

import ELK from 'elkjs/lib/elk.bundled.js';
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
import '@xyflow/react/dist/style.css';

import { nodeTypes } from '@/components/workflow/nodeTypes';


const NodeTypeMapping = {
    TRANSFORM: "transform",
    CONNECTION: "connection",
    BRANCH: "branch",
    TERMINATE: "terminate",
    INPUT: "input-node",
    COMPONENT: "component",
};


function LayoutFlow({ policyId, onNodeClick, onPaneClick }) {
    const [graphData, setGraphData] = useState([]);
    const [componentsState, setComponentsState] = useState([]);
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const { fitView } = useReactFlow();

    const elk = new ELK();

    const elkOptions = {
        'elk.algorithm': 'layered',
        'elk.layered.nodePlacement.strategy': 'SIMPLE',
        'elk.layered.nodePlacement.bk.fixedAlignment': 'BALANCED',
        'elk.layered.spacing.nodeNodeBetweenLayers': 50,
        'elk.spacing.nodeNode': 80,
        'elk.aspectRatio': 1.0,
        'elk.center': true,
        'elk.direction': 'DOWN',
    };

    const loadAndLayout = () => {
        getPolicyVersionData(policyId).then((policyVersionData) => {
            const data = JSON.parse(policyVersionData.graph_definition);
            setGraphData(data);
            console.log(data);

            const components = Object.values(data).filter(
                (node) => node.node_type === "COMPONENT"
            );
            const states = components.map((c) => ({ [c.name]: { isOpen: false } }));
            const componentsState = Object.assign({}, ...states)
            setComponentsState(componentsState);
            console.log(componentsState);

            assembleGraph(data, componentsState, elk, elkOptions)
                .then(([layoutedNodes, layoutedEdges]) => {
                    setNodes(layoutedNodes);
                    setEdges(layoutedEdges);
                    window.requestAnimationFrame(() => fitView());
                });
        });
    };

    const onLayout = useCallback(loadAndLayout, []);

    // Calculate the initial layout on mount.
    useLayoutEffect(() => {
        onLayout();
    }, []);

    const resetClick = () => {
        const newNodes = nodes.map((n) => {
            n.data.clicked = false;
            return n;
        });
        setNodes(newNodes);
    };

    const clickNode = (e, node) => {
        console.log(node);
        resetClick();

        if (node.data.type === "COMPONENT") {
            const newComponentsState = { ...componentsState };
            newComponentsState[node.id].isOpen = !newComponentsState[node.id].isOpen;
            setComponentsState(newComponentsState);

            assembleGraph(graphData, newComponentsState, elk, elkOptions)
                .then(([layoutedNodes, layoutedEdges]) => {
                    setNodes(layoutedNodes);
                    setEdges(layoutedEdges);
                    window.requestAnimationFrame(() => fitView());
                });
            onNodeClick(e, []);
            return;
        }

        const newNodes = nodes.map((n) => {
            if (n.id === node.id) {
                n.data.clicked = true;
            }
            return n;
        });
        setNodes(newNodes);
        onNodeClick(e, node);
    };

    const clickPane = (e) => {
        resetClick();
        onPaneClick(e);
    };

    return (
        <ReactFlowProvider>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeClick={clickNode}
                onPaneClick={clickPane}
                nodeTypes={nodeTypes}
                connectionLineType={ConnectionLineType.SmoothStep}
                fitViewOptions={{ maxZoom: 1 }}
                fitView
            >
                <Background color="#ccc" variant={BackgroundVariant.Dots} />
                <MiniMap nodeStrokeWidth={3} zoomable pannable />
                <Controls />
            </ReactFlow>
        </ReactFlowProvider>
    );
}

export default function Workflow({ policyId, onNodeClick, onPaneClick }) {
    return (
        <ReactFlowProvider>
            <LayoutFlow policyId={policyId} onNodeClick={onNodeClick} onPaneClick={onPaneClick} />
        </ReactFlowProvider>
    );
}


function makeGraphElements(graphData, options) {

    function makeNodes(node, options, parent = null) {
        const nodeWidth = 210;
        const nodeHeight = 42;

        let nodeConfig = {
            id: node.name,
            data: {
                label: node.name,
                description: node.description,
                type: node.node_type,
                dependencies: node.dependencies,
            },

            // Hardcode a width and height for elk to use when layouting.
            width: nodeWidth,
            height: nodeHeight,
        };

        if (parent) {
            nodeConfig.parentId = parent.name;
            nodeConfig.parentReference = parent.metadata.reference;
        }

        if (node.node_type === 'COMPONENT') {
            nodeConfig.children = Object.values(node.metadata.nodes).map(
                (n) => makeNodes(n, options, node)
            );
            nodeConfig.layoutOptions = options;
            nodeConfig.type = "group";
            return nodeConfig;
        }

        if (Object.keys(NodeTypeMapping).includes(node.node_type)) {
            nodeConfig.type = NodeTypeMapping[node.node_type];
        } else {
            nodeConfig.type = 'default';
            nodeConfig.targetPosition = 'top';
            nodeConfig.sourcePosition = 'bottom';
        }

        if (node.metadata !== null) {
            Object.entries(node.metadata).map(([key, value]) => {
                nodeConfig.data[key] = value;
            });
        }

        return nodeConfig;
    }

    function makeEdges(node, nodesMap) {
        if (node.dependencies === null) {
            return [];
        }

        function __makeEdges(node, isComponentIO = false) {
            return node.dependencies.flatMap((dep) => {
                // TODO: If `dep` is an object, it means that it comes from
                // a specific output of a node. For now, we discard it, as
                // we don't display the node outputs.
                if (typeof dep === 'object' && dep !== null) {
                    dep = dep.node;
                }

                const edge = {
                    id: `${dep}-${node.name}`,
                    source: dep,
                    target: node.name,
                    isComponentIO: isComponentIO,
                };

                if (nodesMap[node.name].parentId) {
                    edge.toComponentChild = true;
                    edge.toComponent = nodesMap[node.name].parentId;
                }

                // In order for Elk to layout the edges correctly when the
                // dependency is the output of a Component, we need to add
                // an edge between the Component and the target node.
                const depNode = nodesMap[dep];

                if (depNode.parentId) {
                    edge.fromComponentChild = true;
                    edge.fromComponent = depNode.parentId;

                    if (nodesMap[node.name].parentId != depNode.parentId) {
                        const parentEdge = {
                            id: `${depNode.parentId}-${node.name}`,
                            source: depNode.parentId,
                            target: node.name,
                            isComponentIO: true,
                        };
                        return [edge, parentEdge];
                    }
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
        if (node.children) {
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

    return [structuredNodes, edges];
}


async function assembleGraph(graphData, componentsState, elk, options) {
    const [nodes, edges] = makeGraphElements(graphData, options);

    const modifiedNodes = nodes.filter((node) => {
        return !node.parentId || componentsState[node.parentId].isOpen;
    });
    modifiedNodes.forEach((node) => {
        if (node.data.type === "COMPONENT" && !componentsState[node.id].isOpen) {
            node.children = [];
            node.type = NodeTypeMapping.COMPONENT;
        }
    });
    const modifiedEdges = edges.filter((edge) => {
        const fromChildOfClosedComponent = (
            edge.fromComponentChild && !componentsState[edge.fromComponent].isOpen
        );
        const toChildOfClosedComponent = (
            edge.toComponentChild && !componentsState[edge.toComponent].isOpen
        );
        return !(fromChildOfClosedComponent || toChildOfClosedComponent);
    });

    const [layoutedNodes, layoutedEdges] = await getLayoutedElements(
        modifiedNodes, modifiedEdges, elk, options
    );

    // Filter out the edges that come into or frow from open Components
    // (otherwise ReactFlow will raise several warnings).
    const filteredEdges = layoutedEdges.filter((edge) => {
        const fromOpenComponent = (
            edge.isComponentIO &&
            (componentsState[edge.source] && componentsState[edge.source].isOpen)
        );
        const toOpenComponent = (
            edge.isComponentIO &&
            (componentsState[edge.target] && componentsState[edge.target].isOpen)
        );
        return !(fromOpenComponent || toOpenComponent);
    });
    console.log(layoutedNodes, filteredEdges);

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
            };

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