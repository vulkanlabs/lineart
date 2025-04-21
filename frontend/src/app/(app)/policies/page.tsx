import { fetchPolicies } from "@/lib/api";
import { Separator } from "@/components/ui/separator";

import { PoliciesTable } from "./policies-table";

export default async function Page() {
    const policies = await fetchPolicies().catch((error) => {
        console.error(error);
        return [];
    });

    return (
        <div className="flex flex-1 flex-col gap-6 p-4 lg:gap-6 lg:p-6">
            <div className="flex flex-col gap-4">
                <h1 className="text-lg font-semibold md:text-2xl">Policies</h1>
                <Separator />
            </div>
            <div>
                <PoliciesTable policies={policies} />
            </div>
        </div>
    );
}
