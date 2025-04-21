import { useCallback } from "react";
import { useShallow } from "zustand/react/shallow";

import { Input } from "@/components/ui/input";

import { useWorkflowStore } from "../store";
import { WorkflowNode } from "./base";

export function DataInputNode({ id, data, selected, height, width }) {
    const { updateNodeData } = useWorkflowStore(
        useShallow((state) => ({
            updateNodeData: state.updateNodeData,
        })),
    );

    const setDataSource = useCallback(
        (status: string) => {
            updateNodeData(id, { ...data, metadata: { data_source: status } });
        },
        [id, data, updateNodeData],
    );

    return (
        <WorkflowNode id={id} selected={selected} data={data} height={height} width={width}>
            <div className="flex flex-col gap-1 space-y-2 p-3">
                <span>Data Source ID:</span>
                <Input
                    type="text"
                    value={data.metadata?.data_source}
                    onChange={(e) => setDataSource(e.target.value)}
                />
            </div>
        </WorkflowNode>
    );
}
