import { stackServerApp } from "@/stack";

import PoliciesPage from "./components";
import { fetchPolicies } from "@/lib/api";

export default async function Page() {
    const user = await stackServerApp.getUser();
    const policies = await fetchPolicies(user).catch((error) => {
        console.error("Failed to fetch policies", error);
        return [];
    });
    return <PoliciesPage policies={policies} />;
}
