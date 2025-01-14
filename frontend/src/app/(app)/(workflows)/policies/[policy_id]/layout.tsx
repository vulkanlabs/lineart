import { stackServerApp } from "@/stack";

import { fetchPolicy } from "@/lib/api";
import { RouteLayout } from "./components";

export default async function Layout(props) {
    const params = await props.params;

    const {
        children
    } = props;

    const user = await stackServerApp.getUser();
    const policy = await fetchPolicy(user, params.policy_id);

    return <RouteLayout policy={policy}>{children}</RouteLayout>;
}
