import { setDataSourceEnvVars } from "@/lib/api";
import { ConfigurationVariablesBase } from "@vulkan-server/ConfigurationVariablesBase";

export async function setDataSourceVariablesAction(
    dataSourceId: string,
    variables: ConfigurationVariablesBase[],
) {
    return await setDataSourceEnvVars(dataSourceId, variables);
}
