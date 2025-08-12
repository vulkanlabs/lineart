// Local imports
import { PoliciesTable as SharedPoliciesTable } from "@vulkanlabs/base";
import { Policy } from "@vulkanlabs/client-open";
import { deletePolicy } from "@/lib/api";
import { CreatePolicyDialog } from "./create-dialog";

export function PoliciesTable({ policies }: { policies: Policy[] }) {
    return (
        <SharedPoliciesTable
            policies={policies}
            config={{
                deletePolicy: (policyId) => deletePolicy(policyId),
                CreatePolicyDialog: <CreatePolicyDialog />,
            }}
        />
    );
}
