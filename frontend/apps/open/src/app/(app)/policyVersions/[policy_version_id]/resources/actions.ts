import { setPolicyVersionVariables } from "@/lib/api";
import { ConfigurationVariablesBase } from "@vulkan/client-open";

export async function setPolicyVersionVariablesAction(
    policyVersionId: string,
    variablesToSave: ConfigurationVariablesBase[],
): Promise<any> {
    return await setPolicyVersionVariables(policyVersionId, variablesToSave);
}
