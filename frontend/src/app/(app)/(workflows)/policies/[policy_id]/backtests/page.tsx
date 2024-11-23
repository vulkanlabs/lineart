import { uploadFileFormAction } from "./actions";
import { FileUploaderPage } from "./components";

export default async function Page({ params }) {
    return <FileUploaderPage uploadFn={uploadFileFormAction} policyVersionId={params.policy_version_id} />;
}
