import { stackServerApp } from "@/stack";
import { Suspense } from "react";

import Loader from "@/components/loader";
import { RunPage } from "@/components/run/run-page-server";

export default async function Page(props) {
    const params = await props.params;
    const user = await stackServerApp.getUser();

    return (
        <div className="flex flex-col w-full h-full overflow-scroll">
            <Suspense fallback={<Loader />}>
                <RunPage user={user} runId={params.run_id} />
            </Suspense>
        </div>
    );
}
