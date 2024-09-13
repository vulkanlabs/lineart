import "@/app/globals.css";


export default function LoginLayout({ children }) {
    return (
        <div className="flex flex-col w-screen h-screen max-h-screen">
            <div className="flex h-full w-full">
                {children}
            </div>
        </div>
    );
}
