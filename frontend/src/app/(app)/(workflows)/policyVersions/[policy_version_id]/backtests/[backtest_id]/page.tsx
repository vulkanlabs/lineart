import { stackServerApp } from "@/stack";

import { fetchBacktest, fetchBacktestStatus } from "@/lib/api";
import { BacktestDetailsPage } from "./components";

export default async function Page({ params }) {
    const user = await stackServerApp.getUser();
    const backtest = await fetchBacktest(user, params.backtest_id).catch((error) => {
        console.error(error);
        return null;
    });

    const backtestStatus = await fetchBacktestStatus(user, params.backtest_id).catch((error) => {
        console.error(error);
        return null;
    });

    if (!backtest || !backtestStatus) {
        return <div>Failed to load backtest, please try refreshing the page.</div>;
    }

    return (
        <BacktestDetailsPage
            policyVersionId={backtest.policy_version_id}
            backtest={backtest}
            backfills={backtestStatus.backfills}
        />
    );
}
