import { ReactFlow, MiniMap, Controls } from '@xyflow/react';

import '@xyflow/react/dist/style.css';

// TODO: we should request this data from the backend for the specific
// policy_id. This data is specific to a given Policy Version ID.
const initialNodes = [
    // TODO: we need to handle positioning
    { id: '1', position: { x: 0, y: 0 }, data: { label: '1' } },
    { id: '2', position: { x: 0, y: 100 }, data: { label: '2' } },
];
const initialEdges = [{ id: 'e1-2', source: '1', target: '2' }];

export default function Page({ params }) {
    return (
        <div className='w-svw max-w-full h-full'>
            <ReactFlow defaultNodes={initialNodes} defaultEdges={initialEdges} fitView>
                <MiniMap nodeStrokeWidth={3} zoomable pannable />

                <Controls />
            </ReactFlow>
        </div>
    );
}