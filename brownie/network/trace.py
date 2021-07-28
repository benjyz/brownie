from typing import Any, Callable
import functools
from brownie.exceptions import RPCRequestError
from brownie.network.transaction import TransactionReceipt
from .web3 import web3

def trace_property(fn: Callable) -> Any:
    # attributes that are only available after querying the tranasaction trace

    @property  # type: ignore
    #TODO!
    def wrapper(self: "TransactionReceipt") -> Any:
        if self.status < 0:
            return None
        if self._trace_exc is not None:
            raise self._trace_exc
        try:
            return fn(self)
        except RPCRequestError as exc:
            if web3.supports_traces:
                # if the node client supports traces, raise the actual error
                raise exc
            raise RPCRequestError(
                f"Accessing `TransactionReceipt.{fn.__name__}` on a {self.status.name.lower()} "
                "transaction requires the `debug_traceTransaction` RPC endpoint, but the node "
                "client does not support it or has not made it available."
            ) from None

    return wrapper

def trace_inspection(fn: Callable) -> Any:
    def wrapper(self: "TransactionReceipt", *args: Any, **kwargs: Any) -> Any:
        if self.contract_address:
            raise NotImplementedError(
                "Trace inspection methods are not available for deployment transactions."
            )
        if self.input == "0x" and self.gas_used == 21000:
            return None
        return fn(self, *args, **kwargs)

    functools.update_wrapper(wrapper, fn)
    return wrapper

def supports_traces(provider) -> bool:
    # Send a malformed request to `debug_traceTransaction`. If the error code
    # returned is -32601 "endpoint does not exist/is not available" we know
    # traces are not possible. Any other error code means the endpoint is open.
    response = provider.make_request("debug_traceTransaction", [])
    return bool(response["error"]["code"] != -32601)
