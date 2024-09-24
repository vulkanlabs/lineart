import { stackServerApp } from "@/stack";
import Link from "next/link";

import { fetchPolicy } from "@/lib/api";
import { LocalNavbar } from "./components";
import { LocalSidebar } from "./sidebar";

export default async function Layout({ params, children }) {
    const policyId = params.policy_id;
    const user = await stackServerApp.getUser();
    const policyData = await fetchPolicy(user, policyId);

    return (
        <div className="flex flex-col w-full h-full">
            <LocalNavbar policyData={policyData} />
            <div className="flex flex-row w-full h-full overflow-scroll">
                <LocalSidebar policyId={policyId} />
                <div className="flex flex-col w-full h-full overflow-scroll">{children}</div>
            </div>
        </div>
    );
}
