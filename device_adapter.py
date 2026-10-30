"""Reserved boundary for a future MTTL-W01 runtime adapter.

The reference protocol is plaintext TCP and has no verified device
authentication. This scaffold intentionally has no listener, provisioning
client, frame parser, or relay command implementation.
"""


class MttlW01Adapter:
    """Placeholder that fails closed until a reviewed adapter is implemented."""

    def __init__(self) -> None:
        self.enabled = False

    def connect(self) -> None:
        raise NotImplementedError(
            "MTTL-W01 runtime adapter is intentionally unimplemented; no switching is available."
        )

    def set_outlet(self, outlet_number: int, on: bool) -> None:
        raise NotImplementedError(
            "Relay commands are disabled until protocol security and hardware tests are reviewed."
        )
