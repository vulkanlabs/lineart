import { useCallback } from "react";
import { SquareX } from "lucide-react";
import { useShallow } from "zustand/react/shallow";
import { Position, type NodeChange } from "@xyflow/react";
import Editor from "@monaco-editor/react";

import { Input } from "@/components/ui/input";
import { BaseHandle } from "@/components/reactflow/base-handle";
import { Button } from "@/components/ui/button";

import { VulkanNode } from "../types";
import { useWorkflowStore } from "../store";
import { WorkflowNode, defaultHandleStyle } from "./base";

export function BranchNode({ id, data, selected, height, width }) {
    const { updateNodeData, onNodesChange } = useWorkflowStore(
        useShallow((state) => ({
            updateNodeData: state.updateNodeData,
            onNodesChange: state.onNodesChange,
        })),
    );

    const setSourceCode = useCallback(
        (code: string) => {
            const metadata = { ...data.metadata, source_code: code, function_code: code };
            updateNodeData(id, { ...data, metadata });
        },
        [id, data, updateNodeData],
    );

    const setBranchChoices = useCallback(
        (choices: string[]) => {
            const metadata = { ...data.metadata, choices: choices };
            updateNodeData(id, { ...data, metadata });
        },
        [id, data, updateNodeData],
    );

    const updateMetadata = useCallback(
        (metadata: any) => {
            const newMetadata = { ...data.metadata, ...metadata };
            updateNodeData(id, { ...data, metadata: newMetadata });
        },
        [id, data, updateNodeData],
    );

    const heightStepSize = 80; // Adjust this value as needed

    const addChoice = useCallback(() => {
        const newHeight = height + heightStepSize;
        const newChoices = [...data.metadata.choices, ""];
        const metadata = { ...data.metadata, choices: newChoices };

        updateNodeData(id, { ...data, metadata, minHeight: newHeight });

        onNodesChange([
            {
                id: id,
                type: "dimensions",
                resizing: true,
                setAttributes: true,
                dimensions: {
                    width: width,
                    height: newHeight,
                },
            },
        ] as NodeChange<VulkanNode>[]);
    }, [id, data, height, width, updateNodeData, onNodesChange]);

    const removeChoice = useCallback(
        (index: number) => {
            const newHeight = height - heightStepSize;
            const newChoices = [...data.metadata.choices];
            newChoices.splice(index, 1);

            const metadata = { ...data.metadata, choices: newChoices };

            updateNodeData(id, { ...data, metadata, minHeight: newHeight });

            // TODO: remove the edge whose source was deleted

            onNodesChange([
                {
                    id: id,
                    type: "dimensions",
                    resizing: true,
                    setAttributes: true,
                    dimensions: {
                        width: width,
                        height: newHeight,
                    },
                },
            ] as NodeChange<VulkanNode>[]);
        },
        [id, data, height, width, updateNodeData, onNodesChange],
    );

    return (
        <WorkflowNode
            id={id}
            selected={selected}
            data={data}
            height={height}
            width={width}
            isOutput
        >
            <div className="h-full flex flex-col gap-1 space-y-2 m-3">
                <div className="h-full rounded-md overflow-hidden">
                    <Editor
                        // width={width}
                        // height={height}
                        language="python"
                        value={data.metadata?.source_code || ""}
                        theme="vs-dark"
                        defaultValue="# some comment"
                        onChange={setSourceCode}
                        options={{
                            minimap: {
                                enabled: false,
                            },
                        }}
                    />
                </div>
                <span>Outputs:</span>
                {data.metadata.choices.map((choice, index) => (
                    <div
                        key={index}
                        className="relative flex flex-row items-center gap-2 p-2 pr-4 border border-gray-300 rounded-md"
                    >
                        <BaseHandle
                            type="source"
                            position={Position.Right}
                            id={`${index}`}
                            style={{ ...defaultHandleStyle }}
                        />
                        <Input
                            type="text"
                            value={choice}
                            onChange={(e) => {
                                const newChoices = [...data.metadata.choices];
                                newChoices[index] = e.target.value;
                                setBranchChoices(newChoices);
                            }}
                        />
                        <Button
                            variant="ghost"
                            className="size-6 p-1"
                            onClick={() => removeChoice(index)}
                        >
                            <SquareX className="stroke-red-700" />
                        </Button>
                    </div>
                ))}
                <div className="flex justify-center">
                    <Button variant="ghost" className="p-1 text-blue-500" onClick={addChoice}>
                        Add output
                    </Button>
                </div>
            </div>
        </WorkflowNode>
    );
}
