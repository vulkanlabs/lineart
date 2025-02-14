// Show 8 digits, but on hover show entire ID
export function ShortenedID({ id, hover = true }: { id: string; hover?: boolean }) {
    return (
        <div className="group flex relative">
            <span className="font-mono">{id.slice(0, 8)}</span>
            {hover && (
                <span className="group-hover:opacity-100 opacity-0 font-mono bg-slate-200 text-xs rounded absolute p-2 z-10 shadow-sm h-fit w-fit -inset-y-2">
                    {id}
                </span>
            )}
        </div>
    );
}
