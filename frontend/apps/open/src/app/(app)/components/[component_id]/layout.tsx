import { InnerNavbar, InnerNavbarSectionProps } from "@/components/inner-navbar";
import { fetchComponent } from "@/lib/api";

export default async function Layout(props: {
    params: Promise<{ component_id: string }>;
    children: React.ReactNode;
}) {
    const params = await props.params;
    const { children } = props;
    const component = await fetchComponent(params.component_id);
    const innerNavbarSections: InnerNavbarSectionProps[] = [
        { key: "Component:", value: component.name },
        { key: "Status:", value: component.status },
    ];

    return (
        <div className="flex flex-row w-full h-full">
            <div className="flex flex-col flex-1 h-full">
                <InnerNavbar sections={innerNavbarSections} />
                <div className="flex-1 h-full">{children}</div>
            </div>
        </div>
    );
}
