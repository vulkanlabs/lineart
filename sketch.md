credit_policy = Policy(
        
    Serasa = Node(
        serasa = IO(serasa_params, ...)
        If(
            serasa["score"] >= 600,
            Status.DENY(reason=Reason.SERASA_BAD),
            Snippet(data, serasa),
        )
    )

Snippet = Node(
        scr = HTTPConnection(scr, ...)
        scr_score = HTTPConnection(serasa, params, ...)
        if scr_score >= 800:
            return Status.DENY(reason=Reason.SCR_BAD)
        elif scr_score >= 400:
            return Status.ANALYSIS(reason=Reason.SCR_MID)
        else:
            return Status.APPROVE
    )
)

results = credit_policy.run(customers, Serasa=Table(...), )
results = credit_policy.run(customers, Serasa=HTTPConnection(...), )


# O que a gente quer poder fazer na UI

## Execução e Monitoramento de Políticas

- Políticas => policy
    - Configurar parâmetros de entrada
    - Nodes
        - Visualizar
        - Adicionar
        - Deletar
    - Monitorar -> 
        - Resultados
        - Frequencia
        - Erros
    - Execuções 
        - Triggar -> run
            - Parametrização
            - Como a gente responde
        - Acompanhar resultado -> check on run / resultado do run
        - Monitorar
            - Tempo
            - Falhas
                - Motivo da falha
- Times
    - Criar
    - Gerenciar membros
    - Criar políticas

## Permitir criar e configurar política via UI

- Node
    - Monitorar as execuções de um pedacinho da política individualmente
        - Quantidade de chamadas
        - Retornos
        - Erros
        - Tempo de execução
    - Criar novo
        - do zero
        - Usando componente como base
    - Testar (rodar um node separado)
- Componentes
    - Criar novo
        - Do zero
        - Transformar um bloco em algo reutilizável
    - Testar
    - Listar usos
- Conectores
    - Parametrização diferente para dev vs prod vs prod batch
        - Permitir testes
        - Permitir rodar em batch com mesma regra, outra config
    - Pré-configurar um conector para uso em políticas
        - Configurações básicas, deixando só os dados de políticas p/ preencher