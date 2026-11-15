# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *


def _address_text(value) -> str:
    if isinstance(value, (bytes, bytearray)):
        return "0x" + bytes(value).hex()
    if hasattr(value, "as_bytes"):
        raw = value.as_bytes
        if isinstance(raw, (bytes, bytearray)):
            return "0x" + bytes(raw).hex()
    return str(value).lower()


class ProbeRegistry(gl.Contract):
    owner: Address
    owner_court: str
    bound: bool
    entries: TreeMap[str, str]
    entry_order: DynArray[str]

    def __init__(self, initial_key: str, initial_value: str):
        self.owner = gl.message.sender_address
        self.owner_court = ""
        self.bound = False
        if not isinstance(initial_key, str) or not 1 <= len(initial_key) <= 80:
            raise gl.vm.UserError("[EXPECTED] initial key length is invalid")
        if not isinstance(initial_value, str) or not 1 <= len(initial_value) <= 400:
            raise gl.vm.UserError("[EXPECTED] initial value length is invalid")
        self.entries[initial_key] = initial_value
        self.entry_order.append(initial_key)

    @gl.public.write
    def bind_court(self, court_address: str) -> None:
        if gl.message.sender_address != self.owner:
            raise gl.vm.UserError("[EXPECTED] only deployer may bind court")
        if self.bound:
            raise gl.vm.UserError("[EXPECTED] court is already bound")
        normalized = _address_text(court_address)
        if not normalized or normalized == "0x0000000000000000000000000000000000000000":
            raise gl.vm.UserError("[EXPECTED] court address cannot be zero")
        self.owner_court = normalized
        self.bound = True

    @gl.public.write
    def append(self, key: str, value: str) -> None:
        if not self.bound or _address_text(gl.message.sender_address) != self.owner_court:
            raise gl.vm.UserError("[EXPECTED] only bound court may append")
        if not isinstance(key, str) or not 1 <= len(key) <= 80:
            raise gl.vm.UserError("[EXPECTED] key length is invalid")
        if not isinstance(value, str) or not 1 <= len(value) <= 400:
            raise gl.vm.UserError("[EXPECTED] value length is invalid")
        if key in self.entries:
            raise gl.vm.UserError("[EXPECTED] key already exists")
        self.entries[key] = value
        self.entry_order.append(key)

    @gl.public.view
    def get(self, key: str) -> str:
        if key not in self.entries:
            raise gl.vm.UserError("[EXPECTED] key does not exist")
        return self.entries[key]

    @gl.public.view
    def count(self) -> int:
        return len(self.entry_order)
