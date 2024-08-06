import { redirect } from "next/navigation";

export default function Page({ params }) {
    redirect(`/policies/${params.policy_id}/workflow`);
}