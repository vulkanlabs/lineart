import { PolicyForm } from "@/components/policy-form";
import { Button } from "@/components/ui/button";

export default function Home() {
    return (
        <div>
            {/* TODO: preencher com tabela de políticas */}
            {/* Check: se vazio, mostra isso; senão mostra a tabela */}
            <main className="flex flex-1 flex-col gap-4 p-4 lg:gap-6 lg:p-6">
                <EmptyPolicyTable />
            </main>

            {/* <PolicyForm /> */}
        </div>
    );
}

function EmptyPolicyTable() {
    return (
        <div>
            <div className="flex items-center">
                <h1 className="text-lg font-semibold md:text-2xl">Políticas</h1>
            </div>
            <div
                className="flex flex-1 items-center justify-center rounded-lg border border-dashed shadow-sm"
                x-chunk="dashboard-02-chunk-1"
            >
                <div className="flex flex-col items-center gap-1 text-center">
                    <h3 className="text-2xl font-bold tracking-tight">
                        Você não tem nenhuma política criada.
                    </h3>
                    <p className="text-sm text-muted-foreground">
                        Crie uma política para começar a tomar decisões.
                    </p>
                    <Button className="mt-4">Criar Política</Button>
                </div>
            </div>
        </div>
    );
}