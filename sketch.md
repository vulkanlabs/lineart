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
            return Status.A
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
