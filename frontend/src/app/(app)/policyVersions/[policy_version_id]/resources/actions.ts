import { setPolicyVersionVariables } from "@/lib/api";
import { ConfigurationVariablesBase } from "@vulkan-server/ConfigurationVariablesBase";

export async function setPolicyVersionVariablesAction(
    policyVersionId: string,
    variablesToSave: ConfigurationVariablesBase[],
): Promise<any> {
    return await setPolicyVersionVariables(policyVersionId, variablesToSave);
}
