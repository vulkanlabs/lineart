import { Suspense } from "react";

import { Loader } from "@vulkan/base";
import { RunPage } from "@/components/run/run-page-server";

export default async function Page(props: { params: Promise<{ run_id: string }> }) {
    const { run_id } = await props.params;
    return (
        <div className="flex flex-col w-full h-full overflow-scroll">
            <Suspense fallback={<Loader />}>
                <RunPage runId={run_id} />
            </Suspense>
        </div>
    );
}
