import { useCallback, useState, useEffect } from "react";
import { useShallow } from "zustand/react/shallow";

import { AssetCombobox, AssetOption } from "@/components/combobox";

import { NodeProps } from "@xyflow/react";
import { VulkanNode } from "@/workflow/types";
import { useWorkflowStore } from "@/workflow/store";
import { fetchPolicyVersionsAction } from "@/workflow/actions";
import { StandardWorkflowNode } from "@/workflow/components/base";
import { PolicyVersion } from "@vulkan-server/PolicyVersion";

export function PolicyNode({ id, data, selected, height, width }: NodeProps<VulkanNode>) {
    const { updateNodeData } = useWorkflowStore(
        useShallow((state) => ({
            updateNodeData: state.updateNodeData,
        })),
    );

    const setPolicyVersionID = useCallback(
        (policy_id: string) => {
            updateNodeData(id, { ...data, metadata: { policy_id: policy_id } });
        },
        [id, data, updateNodeData],
    );

    const [selectedPolicy, setSelectedPolicy] = useState(data.metadata.policy_id || "");
    const [policyOptions, setPolicyOptions] = useState<AssetOption[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    // Fetch policies when component mounts
    useEffect(() => {
        async function fetchPolicies() {
            setIsLoading(true);
            try {
                const versions = await fetchPolicyVersionsAction().catch((error) => {
                    return [];
                });
                const validVersions = versions.filter(
                    (version: PolicyVersion) => version.status === "VALID",
                );

                setPolicyOptions(
                    validVersions.map((version: PolicyVersion) => ({
                        value: version.policy_version_id,
                        label: `${version.alias} (${version.policy_version_id.substring(0, 8)})`,
                    })),
                );
            } catch (error) {
                console.error("Error fetching policies:", error);
                // Handle error appropriately
            } finally {
                setIsLoading(false);
            }
        }

        fetchPolicies();
    }, []);

    return (
        <StandardWorkflowNode id={id} selected={selected} data={data} height={height} width={width}>
            <div className="flex flex-col gap-4 p-4">
                <span>Policy Version:</span>
                <AssetCombobox
                    options={policyOptions}
                    value={selectedPolicy}
                    onChange={(value: string) => {
                        setSelectedPolicy(value);
                        setPolicyVersionID(value);
                        updateNodeData(id, { ...data, metadata: { policy_id: value } });
                    }}
                    placeholder="Select a policy..."
                    searchPlaceholder="Search policies..."
                    isLoading={isLoading}
                    emptyMessage="No policies found."
                />
            </div>
        </StandardWorkflowNode>
    );
}
