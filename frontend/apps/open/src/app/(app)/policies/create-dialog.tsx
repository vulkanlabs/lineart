// Local imports
import { CreatePolicyDialog as SharedCreatePolicyDialog } from "@vulkanlabs/base";
import { createPolicyAction } from "./actions";

export function CreatePolicyDialog() {
    return (
        <SharedCreatePolicyDialog
            config={{
                createPolicy: async (data) => {
                    return await createPolicyAction(data);
                },
            }}
        />
    );
}
