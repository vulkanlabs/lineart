"use client";

import { useCallback, useLayoutEffect } from 'react';
import {
    ReactFlow,
    ReactFlowProvider,
    MiniMap,
    Controls,
    Background,
    BackgroundVariant,
    useNodesState,
    useEdgesState,
    useReactFlow,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import ELK from 'elkjs/lib/elk.bundled.js';
import toposort from 'toposort';


const initialNodes = [
    {
        id: 'A',
        draggable: true,
        style: {
            width: 170,
            height: 140,
        },
    },
    {
        id: 'A-1',
        type: 'input',
        data: { label: 'Child Node 1' },
        draggable: true,
        parentId: 'A',
    },
    {
        id: 'A-2',
        data: { label: 'Child Node 2' },
        draggable: true,
        parentId: 'A',
    },
    {
        id: 'B',
        type: 'output',
        data: null,
        draggable: true,
        style: {
            width: 250,
            height: 450,
            backgroundColor: 'rgba(240,240,240,0.25)',
        },
    },
    {
        id: 'B-1',
        data: { label: 'Child 1' },
        parentId: 'B',
        draggable: true,
    },
    {
        id: 'B-2',
        data: { label: 'Child 2' },
        parentId: 'B',
        draggable: true,
        style: {
            width: 100,
            height: 150,
            backgroundColor: 'rgba(240,0,0,0.25)',
            // backgroundColor: 'rgba(240,240,240,0.25)',
        },
    },
    {
        id: 'B-2-1',
        data: { label: 'Child 2-1' },
        parentId: 'B-2',
        draggable: true,
        style: {
            width: 60,
        },
    },
    {
        id: 'B-2-2',
        data: { label: 'Child 2-2' },
        parentId: 'B-2',
        draggable: true,
        style: {
            width: 60,
        },
    },
    {
        id: 'B-3',
        data: { label: 'Child 3' },
        parentId: 'B',
        draggable: true,
        style: {
            width: 60,
        },
    },
    {
        id: 'C',
        type: 'output',
        data: { label: 'Node C' },
        draggable: true,
    },
];

const initialEdges = [
    { id: 'a1-a2', source: 'A-1', target: 'A-2' },
    { id: 'a2-b', source: 'A-2', target: 'B' },
    { id: 'a2-c', source: 'A-2', target: 'C' },
    { id: 'a-b', source: 'A', target: 'B' },
    { id: 'a-c', source: 'A', target: 'C' },
    { id: 'b1-b2', source: 'B-1', target: 'B-2' },
    { id: 'b21-b22', source: 'B-2-1', target: 'B-2-2' },
    { id: 'b1-b3', source: 'B-1', target: 'B-3' },
];


const elk = new ELK();

const elkOptions = {
    'elk.algorithm': 'layered',
    'elk.layered.spacing.nodeNodeBetweenLayers': '100',
    'elk.spacing.nodeNode': '80',
    'elk.direction': 'DOWN',
};


function parseNodeStructure(nodes) {
    const deps = [];
    const nodeStructure = [];

    nodes.forEach((node) => {
        if (node.parentId) {
            deps.push([node.parentId, node.id]);
        }
    });

    const sortedIds = toposort(nodes.map((node) => [node.id]), deps);
    let sortedNodes = sortedIds.map((id) => nodes.find((node) => node.id === id));
    sortedNodes = sortedNodes.filter((node) => node !== undefined);

    for (let node of sortedNodes) {
        if (node.hasOwnProperty('parentId')) {
            _placeChild(node, nodeStructure);
        }
        else {
            nodeStructure.push(node);
        }
    };

    return nodeStructure.map((node) => _format_node(node));
}

function _placeChild(node, nodeStructure) {
    // console.log(node, nodeStructure);
    if (nodeStructure.length === 0) {
        return;
    }

    const parent = nodeStructure.find((n) => n.id === node.parentId);

    if (parent) {
        if (!parent.children) {
            parent.children = [];
        }
        parent.children.push(node);
        return;
    }

    for (const n of nodeStructure) {
        if (n.children) {
            _placeChild(node, n.children);
        }
    }
}

function _format_node(node) {
    if (node.children) {
        node.children = node.children.map((child) => _format_node(child));
        node.layoutOptions = elkOptions;
    }

    const formattedNode = {
        ...node,
        // Adjust the target and source handle positions based on the layout
        // direction.
        targetPosition: 'top',
        sourcePosition: 'bottom',

        // Hardcode a width and height for elk to use when layouting.
        width: node.style?.width || 80,
        height: node.style?.height || 60,
    };

    return formattedNode;
}


const nodeStructure = parseNodeStructure(initialNodes);
console.log(nodeStructure);


const getLayoutedElements = (nodes, edges, options = {}) => {
    const graph = {
        id: 'root',
        layoutOptions: options,
        children: [{id: 'all', layoutOptions: options, children: nodes}],
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
            console.log("nodes");
            console.log(_nodes);

            return {
                nodes: _nodes,
                edges: layoutedGraph.edges,
            };
        })
        .catch(console.error);
};

function LayoutFlow() {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const { fitView } = useReactFlow();

    const onLayout = useCallback(
        () => {
            getLayoutedElements(nodeStructure, initialEdges, elkOptions).then(
                ({ nodes: layoutedNodes, edges: layoutedEdges }) => {
                    setNodes(layoutedNodes);
                    setEdges(layoutedEdges);

                    window.requestAnimationFrame(() => fitView());
                },
            );
        },
        [nodes, edges],
    );

    // Calculate the initial layout on mount.
    useLayoutEffect(() => {
        onLayout();
    }, []);

    return (
        <div className='w-full max-w-full h-full'>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                fitView
            >
                <Background color="#ccc" variant={BackgroundVariant.Dots} />
                <MiniMap nodeStrokeWidth={3} zoomable pannable />
                <Controls />
            </ReactFlow>
        </div>
    );
}

export default () => (
    <ReactFlowProvider>
        <LayoutFlow />
    </ReactFlowProvider>
);