{
  "active": {"runtime": "${ACTIVE_RUNTIME}", "version": "${ACTIVE_VERSION}"},
  "pools": {
    "gvisor": {
      "v1": "sandbox-gvisor-v1.sandbox.svc.cluster.local:8000",
      "v2": "sandbox-gvisor-v2.sandbox.svc.cluster.local:8000"
    },
    "kata-qemu": {
      "v1": "sandbox-kata-qemu-v1.sandbox.svc.cluster.local:8000",
      "v2": "sandbox-kata-qemu-v2.sandbox.svc.cluster.local:8000"
    },
    "kata-clh": {
      "v1": "sandbox-kata-clh-v1.sandbox.svc.cluster.local:8000",
      "v2": "sandbox-kata-clh-v2.sandbox.svc.cluster.local:8000"
    },
    "gvisor-hyperpod": {
      "v1": "sandbox-gvisor-hyperpod-v1.sandbox.svc.cluster.local:8000",
      "v2": "sandbox-gvisor-hyperpod-v2.sandbox.svc.cluster.local:8000"
    },
    "gvisor-cpu": {
      "v1": "sandbox-gvisor-cpu-v1.sandbox.svc.cluster.local:8000",
      "v2": "sandbox-gvisor-cpu-v2.sandbox.svc.cluster.local:8000"
    },
    "kata-clh-cpu": {
      "v1": "sandbox-kata-clh-cpu-v1.sandbox.svc.cluster.local:8000",
      "v2": "sandbox-kata-clh-cpu-v2.sandbox.svc.cluster.local:8000"
    },
    "kata-qemu-cpu": {
      "v1": "sandbox-kata-qemu-cpu-v1.sandbox.svc.cluster.local:8000",
      "v2": "sandbox-kata-qemu-cpu-v2.sandbox.svc.cluster.local:8000"
    }
  }
}
