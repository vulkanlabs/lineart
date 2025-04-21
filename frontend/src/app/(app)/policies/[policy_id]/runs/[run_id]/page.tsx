import { Suspense } from "react";

import Loader from "@/components/animations/loader";
import { RunPage } from "@/components/run/run-page-server";

export default async function Page(props) {
    const params = await props.params;

    return (
        <div className="flex flex-col w-full h-full overflow-scroll">
            <Suspense fallback={<Loader />}>
                <RunPage runId={params.run_id} />
            </Suspense>
        </div>
    );
}
