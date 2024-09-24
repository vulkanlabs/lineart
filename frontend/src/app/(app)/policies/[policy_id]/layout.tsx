import { stackServerApp } from "@/stack";
import Link from "next/link";

import { fetchPolicy } from "@/lib/api";
import { LocalNavbar, LocalSidebar } from "./_components/navigation";

export default async function Layout({ params, children }) {
    const policyId = params.policy_id;
    const user = await stackServerApp.getUser();
    const policyData = await fetchPolicy(user, policyId);

    return (
        <div className="flex flex-col w-full h-full">
            <LocalNavbar policyData={policyData} />
            {children}
        </div>
    );
}
