"""Evaluation harness that runs inside the sandbox container.

Process layout per evaluation request::

    server (uvicorn, never touches CUDA)
      └── evaluate.py   trusted parent: static policy, reference outputs, reference timing
            └── runner.py   untrusted child: imports candidate code, writes outputs + timings

The isolation runtime (gVisor or Kata) protects the node from all three processes. The
process split protects reward integrity: a crash or a corrupted CUDA context in candidate code
cannot change how the reference is computed.
"""

# Bump when the measurement contract changes (seeds, tolerances, timing method). The trainer
# logs this value next to every reward so that a reward shift can be traced to a harness change.
HARNESS_VERSION = "1"
