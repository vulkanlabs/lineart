import { setDataSourceEnvVars } from "@/lib/api";
import { ConfigurationVariablesBase } from "@vulkan/client-open/models/ConfigurationVariablesBase";

export async function setDataSourceVariablesAction(
    dataSourceId: string,
    variables: ConfigurationVariablesBase[],
) {
    return await setDataSourceEnvVars(dataSourceId, variables);
}
