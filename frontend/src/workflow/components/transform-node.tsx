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
        (code: string | undefined) => {
            updateNodeData(id, { ...data, metadata: { source_code: code || "" } });
        },
        [id, data, updateNodeData],
    );

    return (
        <WorkflowNode id={id} selected={selected} data={data} height={height} width={width}>
            <div className="p-3 h-full flex-grow">
                <div
                    className="rounded-md overflow-hidden h-full flex-grow nodrag"
                    onMouseDown={(e) => e.stopPropagation()}
                >
                    <Editor
                        language="python"
                        value={data.metadata?.source_code || ""}
                        theme="vs-dark"
                        defaultValue="# your code here"
                        onChange={setSourceCode}
                        options={{
                            minimap: {
                                enabled: false,
                            },
                            automaticLayout: true,
                        }}
                    />
                </div>
            </div>
        </WorkflowNode>
    );
}
