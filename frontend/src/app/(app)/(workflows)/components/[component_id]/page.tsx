import { stackServerApp } from "@/stack";

import { fetchComponentVersions, fetchComponentVersionUsage } from "@/lib/api";
import { ComponentVersionsTable, ComponentVersionDependenciesTable } from "./components";

export default async function Page({ params }) {
    const user = await stackServerApp.getUser();
    const componentVersions = await fetchComponentVersions(user, params.component_id).catch(
        (error) => console.error(error),
    );

    const componentVersionDependencies = await fetchComponentVersionUsage(
        user,
        params.component_id,
    ).catch((error) => console.error(error));

    return (
        <div className="flex flex-1 flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            <div>
                <div className="flex items-center">
                    <h1 className="text-lg font-semibold md:text-2xl">Versions</h1>
                </div>
                <ComponentVersionsTable versions={componentVersions} />
            </div>
            <div>
                <div className="flex flex-col justify-start">
                    <h1 className="text-lg font-semibold md:text-2xl">Usage Information</h1>
                    <ComponentVersionDependenciesTable entries={componentVersionDependencies} />
                </div>
            </div>
        </div>
    );
}
