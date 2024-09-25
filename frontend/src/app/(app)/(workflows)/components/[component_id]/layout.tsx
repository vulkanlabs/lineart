import { stackServerApp } from "@/stack";

import { InnerNavbarSectionProps, InnerNavbar } from "@/components/inner-navbar";
import { fetchComponent } from "@/lib/api";

export default async function Layout({ params, children }) {
    const user = await stackServerApp.getUser();
    const component = await fetchComponent(user, params.component_id).catch((error) =>
        console.error(error),
    );
    const innerNavbarSections: InnerNavbarSectionProps[] = [
        { key: "Component:", value: component.name },
    ];
    
    return (
        <div className="flex flex-col w-full h-full">
            <InnerNavbar sections={innerNavbarSections}/>
            {children}
        </div>
    );
}
