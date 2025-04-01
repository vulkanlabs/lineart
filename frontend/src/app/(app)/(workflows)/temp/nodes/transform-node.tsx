import { useCallback, useState } from "react";

import { useShallow } from "zustand/react/shallow";
import Editor from "@monaco-editor/react";

import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

import { useWorkflowStore } from "../store";
import { WorkflowNode } from "./base";

export function TransformNode({ id, data, selected, height, width }) {
    const { updateNodeData } = useWorkflowStore(
        useShallow((state) => ({
            updateNodeData: state.updateNodeData,
        })),
    );

    const setSourceCode = useCallback(
        (status: string) => {
            updateNodeData(id, { ...data, metadata: { sourceCode: status } });
        },
        [id, data, updateNodeData],
    );

    return (
        <WorkflowNode id={id} selected={selected} data={data} height={height} width={width}>
            <div className="flex flex-col gap-1 space-y-2 p-3">
                <span>Source code:</span>
                <div className="rounded-md overflow-hidden">
                    <Editor
                        // width={width}
                        height={height * 0.5}
                        language="python"
                        value={data.metadata?.sourceCode || ""}
                        theme="vs-dark"
                        defaultValue="// some comment"
                        onChange={setSourceCode}
                    />
                </div>
            </div>
        </WorkflowNode>
    );
}
