from pydantic import BaseModel

SchemaType = dict[str, type]
JsonSchemaType = dict[str, str]

class ComponentConfig(BaseModel):
    input_schema: JsonSchemaType
    instance_params_schema: JsonSchemaType
    node_definitions: dict[str, dict]
