import { useCallback } from "react";

import { useShallow } from "zustand/react/shallow";
import Editor from "@monaco-editor/react";

import { useWorkflowStore } from "../store";
import { WorkflowNode } from "./base";
import { NodeProps } from "@xyflow/react";
import { VulkanNode } from "../types";

export function TransformNode({ id, data, selected, height, width }: NodeProps<VulkanNode>) {
    const { updateNodeData } = useWorkflowStore(
        useShallow((state) => ({
            updateNodeData: state.updateNodeData,
        })),
    );

    const setSourceCode = useCallback(
        (code: string) => {
            updateNodeData(id, { ...data, metadata: { source_code: code } });
        },
        [id, data, updateNodeData],
    );

    return (
        <WorkflowNode id={id} selected={selected} data={data} height={height} width={width}>
            <div className="flex flex-col gap-1 space-y-2 p-3">
                <div className="rounded-md overflow-hidden">
                    <Editor
                        // width={width}
                        height={height * 0.5}
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
            </div>
        </WorkflowNode>
    );
}
