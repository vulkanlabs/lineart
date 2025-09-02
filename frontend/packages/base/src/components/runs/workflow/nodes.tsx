import React from "react";
import { Handle, NodeTypes, Position } from "@xyflow/react";
import { CheckCircle2, XCircle, Clock, Play, Zap, Terminal, ArrowRightCircle } from "lucide-react";

import { cn } from "@/lib/utils";

interface NodeData {
    label: string;
    type: string;
    clicked?: boolean;
    run?: {
        metadata?: {
            error?: any;
            start_time?: number;
            end_time?: number;
        };
        output?: any;
    };
}

function getNodeStatus(data: NodeData): "error" | "success" | "skipped" {
    if (!data.run) return "skipped";
    if (data.run.metadata?.error) return "error";
    return "success";
}

function getStatusIcon(status: string, size: number = 14) {
    switch (status) {
        case "success":
            return <CheckCircle2 size={size} className="text-green-600" />;
        case "error":
            return <XCircle size={size} className="text-red-600" />;
        case "skipped":
            return <Clock size={size} className="text-gray-400" />;
        default:
            return null;
    }
}

function getNodeTypeIcon(type: string, size: number = 14) {
    switch (type?.toLowerCase()) {
        case "action":
            return <Zap size={size} className="text-gray-600" />;
        case "terminal":
        case "terminate":
            return <Terminal size={size} className="text-gray-600" />;
        case "input":
            return <Play size={size} className="text-gray-600" />;
        default:
            return <ArrowRightCircle size={size} className="text-gray-600" />;
    }
}

function NodeBase({
    data,
    width = 180,
    height = 60,
    isOutput = false,
}: {
    data: NodeData;
    width?: number;
    height?: number;
    isOutput?: boolean;
}) {
    const status = getNodeStatus(data);
    const duration =
        data.run?.metadata?.start_time && data.run?.metadata?.end_time
            ? ((data.run.metadata.end_time - data.run.metadata.start_time) * 1000).toFixed(0) + "ms"
            : null;

    const statusStyles = {
        error: "bg-red-50 border-red-300 hover:border-red-400 hover:shadow-red-100",
        success: "bg-green-50 border-green-300 hover:border-green-400 hover:shadow-green-100",
        skipped: "bg-gray-50 border-gray-300 hover:border-gray-400 hover:shadow-gray-100",
    };

    return (
        <div
            style={{ width, height }}
            className={cn(
                "relative rounded-lg border-2 transition-all duration-200",
                "hover:shadow-lg cursor-pointer",
                statusStyles[status],
                data.clicked && "ring-2 ring-blue-500 ring-offset-2",
            )}
        >
            <Handle
                type="target"
                position={Position.Left}
                className="!w-2 !h-2 !bg-gray-400 !border-2 !border-white"
            />

            <div className="flex flex-col items-center justify-center h-full px-3 relative">
                {/* Status icon in top right */}
                <div className="absolute top-1 right-1">{getStatusIcon(status)}</div>

                {/* Node type icon and label */}
                <div className="flex items-center gap-1.5">
                    {getNodeTypeIcon(data.type, 12)}
                    <span className="text-xs font-medium text-gray-700 truncate max-w-[120px]">
                        {data.label}
                    </span>
                </div>

                {/* Duration badge if available */}
                {duration && (
                    <div className="absolute -bottom-2 right-1">
                        <span className="text-[10px] text-gray-500 bg-white px-1.5 py-0.5 rounded-full border border-gray-200">
                            {duration}
                        </span>
                    </div>
                )}
            </div>

            {!isOutput && (
                <Handle
                    type="source"
                    position={Position.Right}
                    className="!w-2 !h-2 !bg-gray-400 !border-2 !border-white"
                />
            )}
        </div>
    );
}

export function CommonNode({
    data,
    width,
    height,
}: {
    data: any;
    width?: number;
    height?: number;
}) {
    return <NodeBase data={data} width={width} height={height} />;
}

export function TerminateNode({
    data,
    width,
    height,
}: {
    data: any;
    width?: number;
    height?: number;
}) {
    return <NodeBase data={data} width={width} height={height} isOutput />;
}

export function InputNode({ width = 120, height = 50 }: { width?: number; height?: number }) {
    return (
        <div
            style={{ width, height }}
            className={cn(
                "relative rounded-lg border-2 border-gray-600 bg-gray-700 text-white",
                "flex items-center justify-center",
                "hover:shadow-lg transition-all duration-200",
                "hover:bg-gray-600",
            )}
        >
            <div className="flex items-center gap-2">
                <ArrowRightCircle size={14} className="text-gray-300" />
                <span className="text-sm font-medium">Input</span>
            </div>
            <Handle
                type="source"
                position={Position.Right}
                className="!w-2 !h-2 !bg-gray-400 !border-2 !border-white"
            />
        </div>
    );
}

export const nodeTypes = {
    common: CommonNode,
    entry: InputNode,
    terminate: TerminateNode,
} satisfies NodeTypes;
