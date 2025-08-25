import { SharedPoliciesTable } from "@vulkanlabs/base";
import { Policy } from "@vulkanlabs/client-open";
import { deletePolicyClient } from "@/lib/api-client";
import { CreatePolicyDialog } from "./create-dialog";

export function PoliciesTable({ policies }: { policies: Policy[] }) {
    return (
        <SharedPoliciesTable
            policies={policies}
            config={{
                deletePolicy: deletePolicyClient,
                CreatePolicyDialog: <CreatePolicyDialog />,
            }}
        />
    );
}
