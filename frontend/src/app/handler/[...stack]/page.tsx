import { StackHandler } from "@stackframe/stack";
import { stackServerApp } from "@/stack";

import Navbar from "@/components/navbar";

export default async function Handler(props: unknown) {
    return (
        <div className="flex flex-col w-screen h-screen max-h-screen">
            <header className="sticky flex h-16 min-h-16 items-center gap-4 border-b-2 bg-background px-4 md:px-6">
                <Navbar />
            </header>
            <div className="overflow-scroll">
                <StackHandler fullPage app={stackServerApp} routeProps={props} />
            </div>
        </div>
    );
}
