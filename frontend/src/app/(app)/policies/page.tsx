import { stackServerApp } from "@/stack";

import PoliciesPage from "./components";
import { fetchPolicies } from "@/lib/api";

export default async function Page() {
    const user = await stackServerApp.getUser();
    const policies = await fetchPolicies(user);
    return <PoliciesPage policies={policies} />;
}
