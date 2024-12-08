# aws-spot-advisor-sejto

Sejto aims to provide a bit better filtering capabilities of AWS Spot instances
than [AWS Spot Advisor]'s website. What's missing there for me? Filtering in
general.

Imagine yourself in your low-tech company running workloads on AWS Spot
instances and you notice that those Spot instances are being interrupted more
than usual. That's nothing unusual since availability of Spot instances changes
over time. You need to find a suitable alternative within budget. You don't need
bare metal machine or huge VM, just something with similar specification for a
reasonable price. Perhaps you cannot run your workload on Graviton instances,
therefore these are off the table as well.

Despite AWS Spot Advisor is a good tool, it will happily show you instances that
you don't want and need right now. And that's where Sejto comes in since it
offers the same capabilities as AWS Spot Advisor with some additional features.

AWS Spot Advisor features:

* filter by min vCPU
* filter by min memory
* filter EMR-only
* filter by OS
* filter by region

on top of that Sejto enables you to:

* filter by max vCPU
* filter by max memory
* filter by min/max interrupts
* filter by min/max savings
* filter out either bare metal or VM instances
* output in text, CSV and JSON format

## Example usage

Example usage for Linux instances:

```Bash
$ ./aws_spot_advisor_sejto.py \
    --region us-east-1 \
    --os Linux \
    --savings-min 60 \
    --inters-max=15 \
    --exclude-metal \
    --vcpu-min 2 \
    --mem-max 64
instance_type=t3.nano vcpus=2 mem_gb=0.5 savings=90% interrupts=<5%
instance_type=c8g.large vcpus=2 mem_gb=4.0 savings=87% interrupts=<5%
instance_type=inf2.xlarge vcpus=4 mem_gb=16.0 savings=85% interrupts=<5%
[...]
instance_type=m8g.2xlarge vcpus=8 mem_gb=32.0 savings=88% interrupts=5-10%
instance_type=m8g.large vcpus=2 mem_gb=8.0 savings=85% interrupts=5-10%
instance_type=c8g.4xlarge vcpus=16 mem_gb=32.0 savings=85% interrupts=5-10%
instance_type=m8g.xlarge vcpus=4 mem_gb=16.0 savings=85% interrupts=5-10%
instance_type=c7gn.large vcpus=2 mem_gb=4.0 savings=85% interrupts=5-10%
instance_type=c7gn.2xlarge vcpus=8 mem_gb=16.0 savings=81% interrupts=5-10%
[...]
```

And example usage for Windows instances:

```Bash
$ ./aws_spot_advisor_sejto.py \
    --region us-east-1 \
    --os Windows \
    --savings-min 60 \
    --inters-max=15 \
    --exclude-metal \
    --vcpu-min 2 \
    --mem-max 64
instance_type=t2.2xlarge vcpus=8 mem_gb=32.0 savings=77% interrupts=<5%
instance_type=i3en.xlarge vcpus=4 mem_gb=32.0 savings=64% interrupts=<5%
instance_type=t3.medium vcpus=2 mem_gb=4.0 savings=62% interrupts=<5%
instance_type=r6idn.large vcpus=2 mem_gb=16.0 savings=61% interrupts=<5%
instance_type=g4ad.xlarge vcpus=4 mem_gb=16.0 savings=61% interrupts=<5%
instance_type=g5.xlarge vcpus=4 mem_gb=16.0 savings=76% interrupts=5-10%
instance_type=g4dn.xlarge vcpus=4 mem_gb=16.0 savings=67% interrupts=5-10%
instance_type=d3en.4xlarge vcpus=16 mem_gb=64.0 savings=67% interrupts=5-10%
instance_type=r7iz.large vcpus=2 mem_gb=16.0 savings=60% interrupts=5-10%
```

## Possible planned features

* show cost/pricing
* web UI

## Data structures

### Spot Advisor

Example:

```Python
>>> data["global_rate"]
'<10%'
>>> data['instance_types']['r8g.24xlarge']
{'emr': True, 'cores': 96, 'ram_gb': 768.0}
>>> data['ranges']
[
  {'index': 0, 'label': '<5%', 'dots': 0, 'max': 5},
  {'index': 1, 'label': '5-10%', 'dots': 1, 'max': 11},
  [...]
]
>>> data['spot_advisor']['us-east-1']['Linux']['r5.16xlarge']
{'s': 82, 'r': 4}
```

* `global_rate` - global rate of interruptions(I guess)
* `instance_types` - list of AWS instances and their parameters
  * `emr` - whether instance supports EMR
  * `cores` - number of vCPUs
  * `ram_gb` - amount of RAM in GB
* `ranges` - lookup/aggregation table for `spot_advisor`
* `spot_advisor` - approximate savings and interruptions in given region, for
  given OS and AWS instance
  * `s` - savings in percent
  * `r` - interrupt range, lookup in `ranges`


[AWS Spot Advisor]: https://aws.amazon.com/ec2/spot/instance-advisor/
