import Image from 'next/image';
import { Handle, Position } from '@xyflow/react';

import { Split, Blocks } from "lucide-react";
import HttpIcon from '@mui/icons-material/Http';
import OutputIcon from '@mui/icons-material/Output';

import { cn } from "@/lib/utils";
import PythonLogo from "/public/python-logo.png";


function NodeBase({ icon, data, width, height, isOutput = false }) {
    return (
        <div
            style={{ width: width, height: height }}
            className={cn(
                "bg-white border border-black rounded-sm hover:border-2 text-xs",
                data?.clicked ? "border-yellow-400 border-2" : ""
            )}
        >
            <Handle type="target" position={Position.Top} />
            <div className="flex flex-row items-center">
                <div style={{ height: height }} className="flex flex-row items-center border-r">
                    <div className="mx-2">{icon}</div>
                </div>
                <div className="pl-2 w-full">{data.label}</div>
            </div>
            {isOutput ? null : <Handle type="source" position={Position.Bottom} />}
        </div>
    );
}

export function HTTPConnectionNode({ data, width, height }) {
    const icon = <HttpIcon className="max-h-5 max-w-5" />;

    return (
        <NodeBase icon={icon} data={data} width={width} height={height} />
    );
}

export function TransformNode({ data, width, height }) {
    const icon = <Image src={PythonLogo} alt="Python logo" className="max-h-5 max-w-5" />;

    return (
        <NodeBase icon={icon} data={data} width={width} height={height} />
    );
}

export function BranchNode({ data, width, height }) {
    const icon = <Split className="max-h-5 max-w-5" />;

    return (
        <NodeBase icon={icon} data={data} width={width} height={height} />
    );
}

export function TerminateNode({ data, width, height }) {
    const icon = <OutputIcon className="max-h-5 max-w-5" />;

    return (
        <NodeBase icon={icon} data={data} width={width} height={height} isOutput />
    );
}

export function InputNode({ width, height }) {
    return (
        <div
            style={{ width: width, height: height, backgroundColor: "black", color: "white" }}
            // We add this class to use the same styles as React Flow's default nodes.
            className="react-flow__node-default"
        >
            <div>Input</div>
            <Handle type="source" position={Position.Bottom} />
        </div>
    );
}

export function ComponentNode({ data, width, height }) {
    const icon = <Blocks className="max-h-5 max-w-5" />;

    return (
        <div
            style={{ width: width, height: height }}
            className={cn(
                "bg-white border border-black rounded-sm hover:border-2 text-xs",
                data?.clicked ? "border-yellow-400 border-2" : ""
            )}
        >
            <Handle type="target" position={Position.Top} />
            <div className="flex flex-row items-center">
                <div style={{ height: height }} className="flex flex-row items-center border-r">
                    <div className="mx-2">{icon}</div>
                </div>
                <div className="pl-2 w-full">{data.label}</div>
            </div>
            <Handle type="source" position={Position.Bottom} />
        </div>
    );
}


export const nodeTypes = {
    'connection': HTTPConnectionNode,
    'transform': TransformNode,
    'input-node': InputNode,
    'branch': BranchNode,
    'terminate': TerminateNode,
    'component': ComponentNode,
};