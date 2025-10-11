import { Policy } from "@vulkanlabs/client-open";
import {
    CreatePolicyDialog as SharedCreatePolicyDialog,
    PoliciesTable as SharedPoliciesTable,
} from "@vulkanlabs/base/components/policies";

import { createPolicy, deletePolicy, fetchPolicies } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function Page() {
    const policies = await fetchPolicies().catch((error) => {
        console.error(error);
        return [];
    });

    return (
        <div className="flex flex-1 flex-col gap-6 p-4 lg:gap-6 lg:p-6">
            <div className="flex flex-col gap-4">
                <h1 className="text-lg font-semibold md:text-2xl">Policies</h1>
                <div className="h-[1px] w-full bg-border" />
            </div>
            <div>
                <PoliciesTable policies={policies} />
            </div>
        </div>
    );
}

function PoliciesTable({ policies }: { policies: Policy[] }) {
    const creationDialog = <SharedCreatePolicyDialog config={{ createPolicy }} />;

    return (
        <SharedPoliciesTable
            policies={policies}
            config={{
                deletePolicy: deletePolicy,
                CreatePolicyDialog: creationDialog,
                resourcePathTemplate: "/policies/{resourceId}/overview",
            }}
        />
    );
}
