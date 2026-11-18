#!/usr/bin/env bash
# Sandbox nodes only: drop new connections from pods to this node.
#
# The VPC CNI network policy agent always allows traffic between a pod and its own node's IP,
# in both directions, so that kubelet probes keep working. On a sandbox node that means
# candidate code could reach node-local daemons (hostNetwork services, metrics ports) even
# under a default-deny NetworkPolicy. This guard drops new pod-to-node connections arriving on
# the VPC CNI veth interfaces (prefix "eni") and keeps replies to host-initiated connections,
# which is what kubelet probes need.
#
# Installed as a systemd unit so that it is re-applied on every boot, before kubelet starts.
set -euo pipefail

cat > /usr/local/sbin/gpusandbox-node-guard <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
iptables -w -N GPUSANDBOX-GUARD 2>/dev/null || iptables -w -F GPUSANDBOX-GUARD
iptables -w -A GPUSANDBOX-GUARD -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN
iptables -w -A GPUSANDBOX-GUARD -j DROP
iptables -w -C INPUT -i eni+ -j GPUSANDBOX-GUARD 2>/dev/null \
  || iptables -w -I INPUT 1 -i eni+ -j GPUSANDBOX-GUARD
EOF
chmod 0755 /usr/local/sbin/gpusandbox-node-guard

cat > /etc/systemd/system/gpusandbox-node-guard.service <<'EOF'
[Unit]
Description=Drop new pod-to-node connections on GPU sandbox nodes
After=network-online.target
Wants=network-online.target
Before=kubelet.service

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/gpusandbox-node-guard
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now gpusandbox-node-guard.service
