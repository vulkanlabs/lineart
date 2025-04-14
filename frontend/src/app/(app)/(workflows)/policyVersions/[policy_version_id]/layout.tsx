
import { fetchPolicy, fetchPolicyVersion } from "@/lib/api";
import { RouteLayout } from "./components";

export default async function Layout(props) {
    const { policy_version_id } = await props.params;
    const { children } = props;

    const policyVersion = await fetchPolicyVersion(policy_version_id);
    const policy = await fetchPolicy(policyVersion?.policy_id);

    return (
        <RouteLayout policy={policy} policyVersion={policyVersion}>
            {children}
        </RouteLayout>
    );
}
