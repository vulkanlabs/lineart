import { stackServerApp } from "@/stack";

import { fetchBacktest, fetchBacktestStatus } from "@/lib/api";
import { BacktestDetailsPage } from "./components";
import { fetchBacktestMetrics } from "@/lib/api";
import { BacktestMetrics, BacktestPlotData } from "./types";

export default async function Page(props) {
    const params = await props.params;
    const backtest = await fetchBacktest(params.backtest_id).catch((error) => {
        console.error(error);
        return null;
    });

    const backtestStatus = await fetchBacktestStatus(params.backtest_id).catch((error) => {
        console.error(error);
        return null;
    });

    if (!backtest || !backtestStatus) {
        return <div>Failed to load backtest, please try refreshing the page.</div>;
    }

    const availability = BacktestMetricAvailability({ backtest });
    const plotData = await getPlotData(backtest, availability);

    return (
        <BacktestDetailsPage
            policyVersionId={backtest.policy_version_id}
            backtest={backtest}
            backfills={backtestStatus.backfills}
            plotData={plotData}
        />
    );
}

async function getPlotData(
    backtest: any,
    availability: BacktestMetrics,
): Promise<Record<string, any>> {
    const plotData: BacktestPlotData = {};
    const backtestId = backtest.backtest_id;

    if (availability.distributionPerOutcome) {
        const data = await fetchBacktestMetrics(backtestId, false).catch((error) => {
            console.error(error);
            return null;
        });
        if (data) {
            plotData.distributionPerOutcome = data;
        }
    }

    if (availability.targetMetrics) {
        const data = await fetchBacktestMetrics(backtestId, true).catch((error) => {
            console.error(error);
            return null;
        });
        if (data) {
            plotData.targetMetrics = data;
        }
    }

    if (availability.eventRate) {
        const data = await fetchBacktestMetrics(backtestId, true, true).catch((error) => {
            console.error(error);
            return null;
        });
        if (data) {
            plotData.eventRate = data;
        }
    }

    return plotData;
}

function BacktestMetricAvailability({ backtest }): BacktestMetrics {
    if (!backtest.calculate_metrics) {
        return {
            distributionPerOutcome: false,
            targetMetrics: false,
            timeMetrics: false,
            eventRate: false,
        };
    }

    return {
        distributionPerOutcome: true,
        targetMetrics: backtest.target_column,
        timeMetrics: backtest.time_column,
        eventRate: backtest.time_column && backtest.target_column,
    };
}
