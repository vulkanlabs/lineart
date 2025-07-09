import { ComponentVersionDependenciesTable } from "@vulkan/base";
import { fetchComponentVersions, fetchComponentVersionUsage } from "@/lib/api";
import { ComponentVersionsTable } from "./components";

export default async function Page(props: { params: Promise<{ component_id: string }> }) {
    const { component_id } = await props.params;
    const componentVersions = await fetchComponentVersions(component_id).catch((error) => {
        console.error(error);
        return [];
    });

    const componentVersionDependencies = await fetchComponentVersionUsage(
        component_id,
    ).catch((error) => {
        console.error(error);
        return [];
    });

    return (
        <div className="flex flex-1 flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            <div>
                <div className="flex items-center">
                    <h1 className="text-lg font-semibold md:text-2xl">Versions</h1>
                </div>
                <div className="mt-4">
                    <ComponentVersionsTable versions={componentVersions} />
                </div>
            </div>
            <div>
                <div className="flex flex-col justify-start">
                    <h1 className="text-lg font-semibold md:text-2xl">Usage Information</h1>
                    <div className="mt-4">
                        <ComponentVersionDependenciesTable entries={componentVersionDependencies} />
                    </div>
                </div>
            </div>
        </div>
    );
}
