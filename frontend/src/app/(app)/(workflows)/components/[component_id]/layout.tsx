import { stackServerApp } from "@/stack";

import { LocalNavbar } from "./components";
import { fetchComponent } from "@/lib/api";

export default async function Layout({ params, children }) {
    const user = await stackServerApp.getUser();
    const component = await fetchComponent(user, params.component_id).catch((error) =>
        console.error(error),
    );
    console.log(component);
    
    return (
        <div className="flex flex-col w-full h-full">
            <LocalNavbar component={component}/>
            {children}
        </div>
    );
}
