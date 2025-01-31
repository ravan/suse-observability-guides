# Monitoring Your SUSE Virtualization Environment

Setting up comprehensive monitoring for your SUSE Virtualization environment ensures you get the best visibility into your virtual machines and infrastructure. While you can monitor your cluster using the SUSE Observability Agent like any standard Kubernetes setup, we’ll also take advantage of additional [KubeVirt metrics](https://kubevirt.io/user-guide/user_workloads/component_monitoring/#metrics-about-virtual-machines) to gain deeper insights.

In this guide, we’ll walk you through setting up monitoring from scratch, creating useful custom views, and collecting specialized virtual machine metrics.

---

## Prerequisites

Before we get started, make sure you have:
- A running SUSE Observability instance
- A SUSE Virtualization cluster up and running
- Your `.env` file properly configured (refer to the main [README](../../../README.md) for setup details)

### Quick Connectivity Check
To ensure you can connect to your cluster, run the following:

```bash
cd suse/virtualization/vmi-metrics
eval $(task common:shell-env)
kubectl get nodes
```

---

## Installing the SUSE Observability Agent

### Step 1: Create a StackPack Instance
First, we need to set up a Kubernetes StackPack instance. The `CLUSTER_NAME` environment variable determines the instance name.

```bash
task install-stackpack-instance
```

### Step 2: Deploy the Agent
Now, deploy the SUSE Observability Agent:

```bash
task common:deploy-observability-agent
```

Once that’s done, log in to your SUSE Observability instance, and you should see your cluster synced up.

---

## Creating a Custom View for Virtual Machines

SUSE Observability allows you to create **custom views** to focus on key components of your virtualization environment. If you’re new to this feature, check out the [custom view documentation](https://docs.stackstate.com/views/k8s-custom-views).

We’ll use [STQL](https://docs.stackstate.com/reference/k8sts-stql_reference) queries to define the view filters.

### Define These Custom Views:
- **VirtControllers:** (label IN ("kubevirt.io:virt-control") AND type = "pod")
- **VirtualMachines:** (label IN ("kubevirt.io:virt-launcher") AND type = "pod")

💡 **Pro Tip:** Star a view to pin it to the left menu for quick access.

---

## Scraping KubeVirt Metrics with OpenTelemetry

Your SUSE Virtualization environment exposes a Kubernetes service called `kubevirt-prometheus-metrics`. We’ll scrape these metrics and send them to SUSE Observability.

For a full list of available metrics, refer to the [KubeVirt metrics documentation](https://kubevirt.io/monitoring/metrics.html#kubevirt).

The best way to scrape these metrics is by using the OpenTelemetry collector with a Prometheus job configuration. Below is a sample configuration:

```yaml
config:
  receivers:
    prometheus:
      config:
        scrape_configs:
        - job_name: 'kubevirt-metrics'
          scrape_interval: 30s
          tls_config:
            insecure_skip_verify: true
          scheme: https
          kubernetes_sd_configs:
            - role: endpoints
              selectors:
                - role: endpoints
                  field: "metadata.name=kubevirt-prometheus-metrics"
```

To deploy the SUSE Observability OpenTelemetry collector (preconfigured with this scraping job), run:

```bash
task deploy-kubevirt-otel-collector
```

You can now view the collected metrics on the **Metrics** page in SUSE Observability.
All metrics begin with **kubevirt_**

![KubeVirt Metrics](./assets/kubevirt_metrics.png)

---

## Adding Custom Dashboard Charts

To visualize your virtual machine metrics effectively, create **custom charts** in SUSE Observability. 
If you’re not familiar with this feature, refer to the [custom charts documentation](https://docs.stackstate.com/metrics/custom-charts/k8s-add-charts#write-the-outline-of-the-metric-binding).

Understanding system-generated metrics can be overwhelming, and interpreting their meaning can be a challenging task.
A great starting point is to look for pre-existing **Grafana dashboards** and convert them into **SUSE Observability** charts.  

## Sample Charts from Existing Grafana Dashboards  

The following sample charts have been sourced from the **Harvester Grafana Dashboard** and the open-source **KubeVirt Monitoring Dashboard**. 
Depending on environment and version the metric's name and tags may sometimes vary. This is a good place to start troubleshooting when no
data is displayed in the chart or if the chart is missing from the dashboard.

#### Control Plane Charts

| Name | Promql |
| ---- | ------ |
| VMI Creation Time | histogram_quantile(0.95, sum(rate(kubevirt_vmi_phase_transition_time_from_creation_seconds_bucket{instance=~"$instance"}[5m])) by (phase, le)) |
| VMI Start Rate | sum(rate(kubevirt_vmi_phase_transition_time_from_creation_seconds_count{phase="Running", instance=~"$instance"}[5m])) by (instance) |
| VMI Phase Transition Latency | histogram_quantile(0.95, sum(rate(kubevirt_vmi_phase_transition_time_seconds_bucket{phase="Failed", instance=~"$instance"}[5m])) by (le,phase)) |
| VMI Count (approx.) | sum(increase(kubevirt_vmi_phase_transition_time_from_creation_seconds_count{phase="Running", instance=~"$instance"}[20m])) by (instance) |
| Work Queue - Add Rate | sum(rate(kubevirt_workqueue_adds_total{job=~".*kubevirt.*", instance=~"$instance"}[1m])) by (instance, name) |
| Work Queue - Depth | kubevirt_workqueue_depth{job=~".*kubevirt.*", instance=~"$instance"} |
| Work Queue - Queue Duration | histogram_quantile(0.99, sum(rate(kubevirt_workqueue_queue_duration_seconds_bucket{job=~".*kubevirt.*", instance=~"$instance"}[1m])) by (instance, name, le)) |
| Work Queue - Work Duration | histogram_quantile(0.99, sum(rate(kubevirt_workqueue_work_duration_seconds_bucket{job=~".*kubevirt.*", instance=~"$instance"}[1m])) by (instance, name, le)) |
| Work Queue - Unfinished Work | kubevirt_workqueue_unfinished_work_seconds{job=~".*kubevirt.*", instance=~"$instance"} |
| Work Queue - Retry Rate | rate(kubevirt_workqueue_retries_total{instance=~"$instance"}[1m]) |
| Work Queue - Longest Running Processor | kubevirt_workqueue_longest_running_processor_seconds{job=~".*kubevirt.*", instance=~"$instance"} |

#### Virtual Machine Instance Charts

| Name | Promql |
| ---- | ------ |
| CPU Usage | topk(${count}, (avg(rate(kubevirt_vmi_vcpu_seconds[5m])) by (domain, name)))  |
| Memory Usage | topk(${count}, ((kubevirt_vmi_memory_available_bytes - kubevirt_vmi_memory_unused_bytes) / kubevirt_vmi_memory_available_bytes)) |
| Storage Read Traffic Bytes | topk(${count}, (irate(kubevirt_vmi_storage_read_traffic_bytes_total[5m])))  |
| Storage Write Traffic Bytes | topk(${count}, (irate(kubevirt_vmi_storage_write_traffic_bytes_total[5m])))  |
| Network Receive Bits | topk(${count}, (irate(kubevirt_vmi_network_receive_bytes_total[5m])*8)) |
| Network Transmit Bits | topk(${count}, (irate(kubevirt_vmi_network_transmit_bytes_total[5m])*8)) |
| Network Receive Packets (2h) | topk(${count}, (delta(kubevirt_vmi_network_receive_packets_total[2h]))) |
| Network Transmit Packets (2h) | topk(${count}, (delta(kubevirt_vmi_network_transmit_packets_total[2h]))) |
| IO Traffic | irate(kubevirt_vmi_storage_write_traffic_bytes_total{namespace="$namespace", name="$vm"}[5m]) |
| IO Time | irate(kubevirt_vmi_storage_write_times_ms_total{namespace="$namespace", name="$vm"}[5m]) |
| IOPS | irate(kubevirt_vmi_storage_iops_write_total{namespace="$namespace", name="$vm"}[5m]) |

### Converting PromQL Variables for SUSE Observability  

In SUSE Observability, metrics are bound to specific topology components using an **STQL query**. 
The component must have **tags** that can be used as parameters in the **PromQL** query to match the metric’s tags.  

#### Example  

Given a Grafana **PromQL** query:  

```promql
kubevirt_workqueue_unfinished_work_seconds{job=~".*kubevirt.*", instance=~"$instance"}
```

We can create the equivalent query for a **SUSE Observability** chart:

```promql
kubevirt_workqueue_unfinished_work_seconds{k8s_cluster_name="${tags.cluster-name}", k8s_pod_name="${name}"}
```

#### Completed chart definition

```yaml
- id: -120
  name: Unfinished Work
  queries:
    - expression: kubevirt_workqueue_unfinished_work_seconds{k8s_cluster_name="${tags.cluster-name}", k8s_pod_name="${name}"}
      alias: '${name}'
  scope:  type in ("pod") and label = "kubevirt.io:virt-controller"
  identifier: urn:stackpack:kubevirt:shared:metric-binding:work-queue-unfinished-work
  unit: s
  chartType: line
  priority: high
  enabled: true
  layout:
    metricPerspective:
      tab: Virtualization
      section: Work Queue
    componentSummary:
      weight: 3
  _type: MetricBinding
```

### Apply to your system

Now that the explanation of the process to create a chart is out of the way, lets apply the definitions to **SUSE Observabilty**

```bash
task upload-metric-bindings
```
When you navigate to a `virt-controller` or `virt-launcher` pod's metric page, you will see the `Virtualizaton` tab

![Virtual Controller Dashboard](./assets/virt-controller.png)

![Virtual Launcher Dashboard](./assets/virt-launcher.png)

## Conclusion

Setting up monitoring like this ensures you’re capturing all the critical details of your SUSE Virtualization environment. 
Now, you’re ready to keep a close eye on your virtual machines and Kubernetes infrastructure with ease! 🚀

