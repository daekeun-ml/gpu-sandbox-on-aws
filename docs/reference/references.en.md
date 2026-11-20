# Selected references

Core sources used throughout the guide. See [Verified facts and sources](sources.md) for specific claims and AWS run records.

<span id="ref-beginner-02-container-vs-sandbox"></span>
<span id="ref-beginner-03-gpu-sandbox"></span>
<span id="ref-concepts-01-why-gpu-sandbox"></span>
<span id="ref-concepts-02-isolation-runtimes"></span>
<span id="ref-concepts-05-decision-guide"></span>
<span id="ref-handson-02-gvisor"></span>
<span id="ref-handson-03-kata"></span>

## Isolation runtimes { #runtimes }

- Runtime selection for pods. [Kubernetes RuntimeClass](https://kubernetes.io/docs/concepts/containers/runtime-class/)
- GPU and driver requirements for nvproxy. [gVisor GPU support](https://gvisor.dev/docs/user_guide/gpu/)
- Feature support in QEMU and Cloud Hypervisor. [Kata hypervisor support](https://github.com/kata-containers/kata-containers/blob/4.3.1/docs/hypervisors.md)
- Instance requirements for Kata CPU. [EC2 nested virtualization](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html)

<span id="ref-beginner-05-hands-on"></span>
<span id="ref-concepts-04-platforms-and-instances"></span>
<span id="ref-getting-started"></span>
<span id="ref-handson-00-overview"></span>
<span id="ref-handson-01-cluster-and-images"></span>
<span id="ref-handson-07-hyperpod"></span>
<span id="ref-handson-09-demo-site"></span>
<span id="ref-handson-10-cpu-only"></span>
<span id="ref-handson-99-cleanup"></span>
<span id="ref-production-00-architecture"></span>
<span id="ref-production-01-capacity-and-nodes"></span>
<span id="ref-production-07-observability-and-operations"></span>
<span id="ref-production-08-cost"></span>
<span id="ref-production-09-cdk"></span>
<span id="ref-reference-glossary"></span>
<span id="ref-reference-repository-map"></span>
<span id="ref-reference-configuration"></span>
<span id="ref-reference-troubleshooting"></span>
<span id="ref-reference-faq"></span>

## AWS deployment and operations { #aws }

- Access requirements for private clusters. [EKS API endpoint access](https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html)
- Stack setup, deployment, and cleanup. [AWS CDK v2](https://docs.aws.amazon.com/cdk/v2/guide/home.html)
- Permissions and cluster prerequisites. [HyperPod EKS prerequisites](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-prerequisites.html)
- Training Jobs and restart configuration. [HyperPod training operator](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator.html)
- NodePools and node disruption. [Karpenter](https://karpenter.sh/docs/)
- Instance rates for cost estimates. [EC2 On-Demand pricing](https://aws.amazon.com/ec2/pricing/on-demand/)

<span id="ref-beginner-01-why-sandbox"></span>
<span id="ref-beginner-06-multi-turn-agent"></span>
<span id="ref-concepts-06-agent-sandbox"></span>
<span id="ref-handson-04-sandbox-pools"></span>
<span id="ref-handson-11-multi-turn"></span>
<span id="ref-production-02-security"></span>
<span id="ref-production-03-gateway-and-pools"></span>

## Access control and episodes { #security-agents }

- Enable VPC CNI network policies. [EKS NetworkPolicy](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html)
- Node credentials and pod permissions. [EKS IAM best practices](https://docs.aws.amazon.com/eks/latest/best-practices/identity-and-access-management.html)
- SandboxClaim and warm pools. [Kubernetes Agent Sandbox](https://github.com/kubernetes-sigs/agent-sandbox)

## AWS technical blogs { #aws-technical-blogs }

This four-part Korean-language series covers EKS-based isolation, a production case study, and how to choose a managed sandbox.

- Isolation architecture and pod and node controls on EKS. [Part 1: EKS and Agent Sandbox fundamentals](https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-1/)
- Experiments with NetworkPolicy, sandbox-router authorization, and warm pools. [Part 2: Network, authorization, and warm pool tests](https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-2/)
- Operating per-project sandboxes and dedicated NodePools. [Part 3: Ably’s Agent Sandbox deployment on EKS](https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-3/)
- Managed sandbox isolation, lifecycle, and selection criteria. [Part 4: Amazon Bedrock AgentCore Runtime](https://aws.amazon.com/ko/blogs/tech/aws-ai-agent-sandbox-eks-isolation-part-4/)
- VM-based workload isolation with Kata on EKS. [Enhancing Kubernetes workload isolation and security using Kata Containers](https://aws.amazon.com/blogs/containers/enhancing-kubernetes-workload-isolation-and-security-using-kata-containers/)

<span id="ref-beginner-04-rl-and-sandbox"></span>
<span id="ref-concepts-03-onpolicy-rl-with-sandboxes"></span>
<span id="ref-handson-05-grpo-training"></span>
<span id="ref-handson-06-sandbox-update"></span>
<span id="ref-handson-08-benchmark"></span>
<span id="ref-production-04-reward-integrity"></span>
<span id="ref-production-05-sandbox-updates"></span>
<span id="ref-production-06-scaling-with-verl"></span>

## Training and evaluation { #training }

- Generation, rewards, and optimizer settings. [TRL GRPOTrainer](https://huggingface.co/docs/trl/main/en/grpo_trainer)
- Distributed RL and reward integration. [veRL](https://github.com/verl-project/verl)
- GPU kernel tasks and performance evaluation. [KernelBench](https://arxiv.org/abs/2502.10517)
- Reward hacking cases observed during evaluation. [KernelBench v0.1](https://scalingintelligence.stanford.edu/blogs/kernelbenchv01/)
