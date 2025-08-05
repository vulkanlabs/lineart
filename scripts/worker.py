from hatchet_sdk import Context, EmptyModel, Hatchet 
from pydantic import BaseModel
 
hatchet = Hatchet(debug=True)
 
class SimpleInput(BaseModel):
    message: str

wf = hatchet.workflow(name="SimpleWorkflow")

@wf.task(name="SimpleTask")
def simple(input: SimpleInput, ctx: Context) -> dict[str, str]:
    return {
      "transformed_message": input.message.lower(),
    }

worker = hatchet.worker(name="test-worker", workflows=[wf])
worker.start()  
