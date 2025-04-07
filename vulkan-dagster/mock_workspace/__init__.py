from dagster import Definitions, job, op


@op
def return_five():
    return 5


@op
def add_one(arg):
    return arg + 1


@job
def do_stuff():
    add_one(return_five())


defs = Definitions(jobs=[do_stuff])
