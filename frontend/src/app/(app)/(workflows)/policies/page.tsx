import { stackServerApp } from "@/stack";

import { PoliciesPage } from "./components";
import { fetchPolicies } from "@/lib/api";

export default async function Page() {
    const policies = await fetchPolicies().catch((error) => {
        console.error(error);
        return [];
    });

    return (
        <div className="flex flex-1 flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            <h1 className="text-lg font-semibold md:text-2xl">Policies</h1>
            <PoliciesPage policies={policies} />
        </div>
    );
}
