import { stackServerApp } from "@/stack";

import { fetchPolicy, fetchPolicyVersion } from "@/lib/api";
import { RouteLayout } from "./components";

export default async function Layout(props) {
    const { policy_version_id } = await props.params;
    const { children } = props;

    const user = await stackServerApp.getUser();
    const policyVersion = await fetchPolicyVersion(policy_version_id);
    const policy = await fetchPolicy(user, policyVersion?.policy_id);

    return (
        <RouteLayout policy={policy} policyVersion={policyVersion}>
            {children}
        </RouteLayout>
    );
}
