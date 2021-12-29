# neustar-interview
take-home interview for Neustar

Runs a script on servers via Ansible, collects and parses a sample of log entries matching a certain pattern (in this case, a specific application's launch latency), and returns the mean and standard deviation of the launch latencies on each server.

## Installation/Requirements
Requires Python 3 and Ansible to run.  Requires Vagrant and virtualbox to deploy the test environment.

* https://www.virtualbox.org/manual/ch02.html
* https://www.vagrantup.com/docs/installation

It is recommended that you use a virtual environment for Python and Ansible:
```bash
$ python3 -m venv venv
$ source venv/bin/activate
(venv)$ pip install ansible
(venv)$ ...(whatever)
(venv)$ deactivate
$
```

## Deploying the test environment
Since the instructions presume this is being run against servers that don't actually exist, it was essential to devise a local test environment to mimick them.  In this case, the 5 servers are deployed as VMs locally on Virtualbox (or whatever virtualization platform you choose) via Vagrant and Ansible.

Presuming you have your virtual environment activated and Ansible installed (see above), you may provision the the local test environment by navigating to the `vagrant` directory and running `vagrant up`.
```bash
(venv)$ vagrant up
```

This will create 5 VMs configured with the `vagrant/playbook.yaml` ansible playbook, which seeds each VM with randomly generated logs using the `scripts/gen-log.py` script:
```bash
$ python3 gen-log.py --help
usage: gen-log.py [-h] [--dest_log_file DEST_LOG_FILE]
                  [--max_latency_range MAX_LATENCY_RANGE]
                  [--max_logs_range MAX_LOGS_RANGE]
                  [--match_string MATCH_STRING]
                  sample_log_path

Randomly generates log files from a sample log.

positional arguments:
  sample_log_path       Location of sample log file.

optional arguments:
  -h, --help            show this help message and exit
  --dest_log_file DEST_LOG_FILE
                        Location of sample log file.
  --max_latency_range MAX_LATENCY_RANGE
                        Max latency range.
  --max_logs_range MAX_LOGS_RANGE
                        Max number of random match entry logs.
  --match_string MATCH_STRING
                        Log entries string to match.
```

It will only do this once, so if you want to regenerate the logs on the VMs, run:
```bash
(venv)$ ansible-playbook regenerate-random-logs-playbook.yaml -i .vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory
```

*NOTE:* Vagrant will generate an Ansible inventory for the VMs at the `.vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory` location.  You will need this when running Ansible playbooks on these servers outside of the Vagrant provisioner.

### SSH Login issues
When running playbooks outside of the Vagrant Ansible provisioner, you may need the following added to your `~/.ssh/config` to avoid ssh login problems:
```
Host 127.0.0.1
    IdentitiesOnly yes
```

## Gathering application launch metrics
To gather the application launch metrics from each server, head to the `metrics/` folder and run the appropriate playbook:

Remote servers:
```bash
(venv)$ ansible-playbook playbook-remote.yaml -i hosts.ini
```

Local Vagrant VMS:
```bash
(venv)$ ansible-playbook playbook-local.yaml -i ../vagrant/.vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory
```

The playbook will run the `scripts/ultradns-latency.py`  script on each server, and return the results from `stdout`:
```bash
$ python3 ultradns-latency.py --help
usage: ultradns-latency.py [-h] [--match_string MATCH_STRING]
                           [--sample_size SAMPLE_SIZE] [--json]
                           log_path

Parse log and return mean/stddev of application launch latencies.

positional arguments:
  log_path              Location of log file to parse.

optional arguments:
  -h, --help            show this help message and exit
  --match_string MATCH_STRING
                        Log entries string to match.
  --sample_size SAMPLE_SIZE
                        Number of most recent log entries to sample.
  --json                Output mean and stddev as machine readable json.
```

## Design Notes

### Language
I choose Python for several reasons: 
1. It's by far my strongest language.
1. It already comes installed on most VM images.
1. It doesn't have to be compiled.
1. Other scripting languages are poorly designed, imo.  Bash isn't designed to be a true programming language and the syntax is incredibly arcane, and I have a personal distaste for Ruby and Javascript.
1. Ansible is written in Python, which means the two scripts can be ported into Ansible modules down the line.

### Infrastructure
Given that the assignment only refers to remote servers that don't actually exist, the primary infrastructure design considerations were for the local test environment.  This means my choices were down to two options: VMs or Containers.

1. Containers are meant to be immutable, and only changed at the image build stage.  Although they can be used kind-of similarly as a VM, this isn't really what they are for.  This makes randomizing the logs for each instance tricky.
1. Since VMs are mutable and configured after the base image is deployed, it makes generating random log files for each server much easier.
1. The remote servers are not described as containers, and  are therefore better represented as full VMs.
1. Vagrant not only makes configuring and deploying local VMs fairly easy, but it comes pre-baked with an Ansible provisioner that sets up everything you need to use Ansible automatically.

So, Vagrant VMs configured with the Ansible provisioner are my choice for the local test environment. We can make-believe about the remote servers since they don't exist, and I'm not messing around with my /etc/hosts to route the URLs to something I'm already running locally.

### Config managment and script execution
The assignment specified Ansible as the means by which this code is to be executed, so alternatives were not considered.  Ansible is good enough, we shall use Ansible.

### Issues
I had the most problems with, and spent the most time just trying to get the test enviornment working.  The code for setting up multiple VMs in Vagrant was challenging in Ruby because Vagrant evaluates outer contexts first, and using nested config structures resulted in strange behavior, with certain configs being ignored while others at the same context level being used.

Also, most of the code found on the internet averaged around 5 years old, and didn't work.  Vagrant and VMs are kind of old-hat in the industry I guess.  Ultimately I found that I didn't need to change most of the default configurations, so I stripped out everything that was unnecessary and let Vagrant do its thing.

The biggest challenge was trying to get playbooks to work with the VMs outside of the Vagrant Ansible provisioner.  It took quite a while of research to figure out two key pieces of information: 
1. That the Vagrant Ansible provisioner generates its own inventory file `.vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory`, which includes the location of the individual ssh private keys that Vagrant generates for each host, along with each host's ssh port mapping.
1. That I needed to add `IdentitiesOnly yes` to host `127.0.0.1` in `~/.ssh/config`. Otherwise, Ansible would try every identity file when connecting to each sever, then each server would block access due to too many invalid login attempts.  This ensures that only the specified identity and cert are used.

### Other approaches
Although this is fine for demonstration purposes and a semi-ad hoc workflow, it isn't ideal. It's too manual, the information isn't being saved anywhere, and it isn't being presented in an ideal context.

A better approach would use Ansible purely for the configuration management of the servers, and modify the script to be run as a regular cron job that returns the host and metrics information to an HA time-series nosql DB, like Cloudwatch Metrics, Google metrics, Influxdb, or Prometheus.  You could also use microservices to deduplicate entries and write/read them from a message queue first, to ensure higher reliability by decoupling the direct connection between the parser and the time-series db. From there, the metrics could be viewed from a metrics dashboard like Grafana, and automatic alerts configured through your pager system of choice.

# Author
* Garrett Anderson <garrett@devnull.rip>
