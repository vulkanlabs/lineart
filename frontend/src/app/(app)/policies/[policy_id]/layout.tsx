import { fetchPolicy } from "@/lib/api";
import { RouteLayout } from "./components";

export default async function Layout(props) {
    const params = await props.params;

    const { children } = props;

    const policy = await fetchPolicy(params.policy_id);

    return <RouteLayout policy={policy}>{children}</RouteLayout>;
}
