import { fetchPolicy, fetchPolicyVersion } from "@/lib/api";
import { RouteLayout } from "./components";

export default async function Layout(props: {
    params: { policy_version_id: string };
    children: React.ReactNode;
}) {
    const { children } = props;

    const policyVersion = await fetchPolicyVersion(props.params.policy_version_id);
    if (!policyVersion) {
        return <div>Policy version not found</div>;
    }

    const policy = await fetchPolicy(policyVersion.policy_id);

    return (
        <RouteLayout policy={policy} policyVersion={policyVersion}>
            {children}
        </RouteLayout>
    );
}
