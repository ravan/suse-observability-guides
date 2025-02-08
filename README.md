# SUSE Observability Guides  

This repository provides a collection of configuration examples for SUSE Observability extensions.  

## Available Guides  

- [SUSE Observability User Interface Extension](./guides/suse/observability/view-customization/README.md) 
- [SUSE Virtualization Observability](./guides/suse/virtualization/metrics/README.md)  

## Prerequisites  

Before using these guides, ensure you have the following tools installed and properly configured:  

- **[SUSE Observability CLI](https://docs.stackstate.com/cli/cli-sts)** – Command-line interface for SUSE Observability.  
- **[Taskfile](https://taskfile.dev/installation/)** – A task runner for automating commands.  
  - Supports tab completion, making it easy to view available tasks.  
- **[Gomplate](https://docs.gomplate.ca/installing/)** – A powerful template processor.  
- **[Helm](https://helm.sh/docs/intro/install/)** – A package manager for Kubernetes.  

## Required Knowledge  

These guides use **[Taskfile](https://taskfile.dev/)** to manage shell commands.
Familiarize yourself with its basics on their official website.  

Additionally, a general working knowledge of **SUSE Observability** is required to effectively use these configurations.  

## Environment 

Create a `.env` file 

```bash
cp env.example .env
```

Change the content with details about your environment.

```bash
# SUSE Observability Instance to use a backend
SO_URL=https://xxx-lab.app.stackstate.io
SO_API_KEY=tmnpPT69Z
SO_TOKEN=xxxxx
SO_OTLP=otlp-xxx-lab.app.stackstate.io
SO_CONTEXT=name of cli context to connecto to SO_URL

# Remote Kubernetes Cluster under observation
LOCAL_CLUSTER=false
CLUSTER_NAME=lab-rav
KUBECONFIG_FILE_PATH=~/sts/repos/github/ravan/observability-examples
KUBECONFIG_FILE_NAME=cloud-kubeconfig

# helm repo add so-addons https://ravan.github.io/helm-charts/
HELM_REPO=so-addons
```

