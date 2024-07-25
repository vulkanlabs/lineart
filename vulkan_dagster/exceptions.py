class UserCodeException(Exception):
    def __init__(self, node_name: str):
        self.node_name = node_name
        super().__init__(f"User code in node {node_name} raised an exception")
