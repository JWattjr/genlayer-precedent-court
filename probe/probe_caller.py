# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *


class ProbeCaller(gl.Contract):
    registry_address: Address
    last_read: str

    def __init__(self, registry_address: str):
        self.registry_address = Address(registry_address)
        self.last_read = ""

    @gl.public.write
    def read_then_emit(self, read_key: str, write_key: str, write_value: str) -> dict:
        registry = gl.get_contract_at(self.registry_address)
        prior_value = registry.view().get(read_key)
        self.last_read = prior_value
        registry.emit(on="finalized").append(write_key, write_value)
        return {"read_value": prior_value, "write_emitted": True}

    @gl.public.view
    def get_last_read(self) -> str:
        return self.last_read
