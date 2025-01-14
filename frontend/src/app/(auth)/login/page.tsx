import { VulkanLogo } from "@/components/logo";
import { SignIn } from "@stackframe/stack";

export default function Page() {
    return (
        <div className="flex flex-col w-screen h-screen min-h-screen" >
            <div className="m-8">
                <VulkanLogo />
            </div>
            <div className="flex m-auto h-fit min-h-64">
                {/* <LoginForm /> */}
                <SignIn
                    fullPage={true}
                    automaticRedirect={true}
                    firstTab='password'
                />
            </div>
        </div>
    )
}