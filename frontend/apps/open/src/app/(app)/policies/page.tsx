import { fetchPolicies } from "@/lib/api";
import { SharedPageTemplate } from "@vulkanlabs/base";
import { PoliciesTable } from "./policies-table";

export const dynamic = "force-dynamic";

export default async function Page() {
    return (
        <SharedPageTemplate 
            config={{
                title: "Policies",
                fetchData: fetchPolicies,
                TableComponent: PoliciesTable,
                requiresProject: false,
                useSeparator: false,
                errorFallback: []
            }}
        />
    );
}
