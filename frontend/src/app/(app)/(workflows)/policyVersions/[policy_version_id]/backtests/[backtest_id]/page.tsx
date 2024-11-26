import { stackServerApp } from "@/stack";

import { fetchBacktestStatus } from "@/lib/api";
import { BacktestDetailsPage } from "./components";

export default async function Page({ params }) {
    const user = await stackServerApp.getUser();
    const backtest = await fetchBacktestStatus(user, params.backtest_id).catch((error) => {
        console.error(error);
        return [];
    });

    return (
        <BacktestDetailsPage policyVersionId={params.policy_version_id} backtest={backtest} />
    );
}
