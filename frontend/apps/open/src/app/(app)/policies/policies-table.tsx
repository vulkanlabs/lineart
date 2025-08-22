import { SharedPoliciesTable } from "@vulkanlabs/base";
import { Policy } from "@vulkanlabs/client-open";
import { deletePolicyAction } from "./actions";
import { CreatePolicyDialog } from "./create-dialog";

export function PoliciesTable({ policies }: { policies: Policy[] }) {
    return (
        <SharedPoliciesTable
            policies={policies}
            config={{
                deletePolicy: deletePolicyAction,
                CreatePolicyDialog: <CreatePolicyDialog />,
            }}
        />
    );
}
