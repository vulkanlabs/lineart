import { Position } from "@xyflow/react";

import { BaseHandle } from "@/components/flow/base-handle";
import { HANDLE_STYLE } from "./base";

export const NODE_SIZE = { width: 260, height: 50 };

export function InputNode({ id, data, selected, height, width }) {
    return (
        <div
            style={{ ...NODE_SIZE, backgroundColor: "black", color: "white" }}
            // We add this class to use the same styles as React Flow's default nodes.
            className="react-flow__node-default"
        >
            <div>Input</div>
            <BaseHandle type="source" position={Position.Right} style={{ ...HANDLE_STYLE }} />
        </div>
    );
}