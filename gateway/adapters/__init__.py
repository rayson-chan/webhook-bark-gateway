from gateway.adapters.generic import GenericAdapter
from gateway.adapters.paseo import PaseoAdapter
from gateway.adapters.tailscale import TailscaleAdapter

ADAPTERS = {
    "generic": GenericAdapter(),
    "paseo": PaseoAdapter(),
    "tailscale": TailscaleAdapter(),
}

