import { Handle, Position } from "@xyflow/react";

import { cn } from "@/lib/utils";

function NodeBase({ data, width, height, isOutput = false }) {
    const status = data.run ? data.run.metadata?.error ? "error" : "success" : "skipped";
    return (
        <div
            style={{ width: width, height: height }}
            className={cn(
                "bg-white border border-black rounded-sm hover:border-2 text-xs",
                status === "error" ? "bg-red-400 border-red-400" : "",
                status === "success" ? "bg-green-400 border-green-400" : "",
                status === "skipped" ? "bg-gray-400 border-gray-400" : "",
                data.clicked ? "border-yellow-400 border-2" : "",
            )}
        >
            <Handle type="target" position={Position.Left} />
            <div className="flex items-center justify-center h-full">
                <div className="w-full overflow-hidden text-ellipsis text-center">{data.label}</div>
            </div>
            {isOutput ? null : <Handle type="source" position={Position.Right} />}
        </div>
    );
}

export function CommonNode({ data, width, height }) {
    return <NodeBase data={data} width={width} height={height} />;
}

export function TerminateNode({ data, width, height }) {
    return <NodeBase data={data} width={width} height={height} isOutput />;
}

export function InputNode({ width, height }) {
    return (
        <div
            style={{ width: width, height: height, backgroundColor: "black", color: "white" }}
            // We add this class to use the same styles as React Flow's default nodes.
            className="react-flow__node-default"
        >
            <div>Input</div>
            <Handle type="source" position={Position.Right} />
        </div>
    );
}

export const nodeTypes = {
    common: CommonNode,
    entry: InputNode,
    terminate: TerminateNode,
};
