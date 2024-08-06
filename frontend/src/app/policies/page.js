import PolicyPageBody from "@/app/policies/policiesPage";

export default function Home() {
    return (
        <div>
            <main className="flex flex-1 flex-col gap-4 p-4 lg:gap-6 lg:p-6">
                <PolicyPageBody/>
            </main>
        </div>
    );
}
