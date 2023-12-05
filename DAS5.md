# Running on DAS5

This document describes instructions for running this project on the [DAS5](https://www.cs.vu.nl/das5/home.shtml)'s compute nodes.

## Connecting to DAS5

The first step is to connect to the DAS5 fileserver, from which you can schedule the jobs to be run on the compute nodes. To connect to this fileserver from outside of the VU network, you'll have to connect to the (proxy) access server. See below or [here](https://www.cs.vu.nl/das5/accounts.shtml) for more details.

For efficiency you can add the following aliases to your `.ssh/config` (read more [here](https://www.howtogeek.com/75007/stupid-geek-tricks-use-your-ssh-config-file-to-create-aliases-for-hosts/)). After adding the aliases you can connect to the fileserver through `ssh DAS5`, you'll be prompted for your VU account password and DAS5 account password, after which you'll be connected to the DAS5 fileserver.

```
Host VUAccessServer
    HostName ssh.data.vu.nl
    User <replace-with-vu-id>

Host DAS5
    HostName fs0.das5.cs.vu.nl
    User <replace-with-DAS5-account-name>
    ProxyJump VUAccessServer
```

## Setup

This section details the steps that should be taken to set up the required Python and Go environment. This set up has to only be performed once per DAS5 account.

We've used the following in our testing.
| Dependency | Version |
|-------|-------|
| Go | go1.21.4 linux/amd64 |
| Python | 3.11.5 |
| Conda | 23.10.0 |
| pipx | 1.3.1 |
| poetry | 1.7.1 |

### Code
First off copy the code over to the fileserver (this assumes you've set up the aliases as discussed above).
``` sh
scp -r ./ DAS5:DLSA
```

### Python Setup

#### 1. Install Python

We use [miniconda3](https://docs.conda.io/projects/miniconda/en/latest/).

```sh
mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm -rf ~/miniconda3/miniconda.sh

~/miniconda3/bin/conda init bash
~/miniconda3/bin/conda init zsh

source ~/.bashrc

conda --version # should print `conda 23.10.0`.
python3 --version # should now print `Python 3.11.5` or higher.
```

#### 2. Install Python dependencies

```sh
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install poetry
poetry install # if this does not work directly then make poetry use the miniconda environment: https://stackoverflow.com/a/75555576
```

### Go Setup

For Go we'll download and unpack it, and then add it to the path persistently.

```sh
wget --output-document ~/.local/lib/go1.21.4.linux-amd64.tar.gz https://go.dev/dl/go1.21.4.linux-amd64.tar.gz
tar -C ~/.local/lib/ -xzf ~/.local/lib/go1.21.4.linux-amd64.tar.gz
rm ~/.local/lib/go1.21.4.linux-amd64.tar.gz
echo "export PATH=$PATH:~/.local/lib/go/bin" >> ~/.bashrc
source ~/.bashrc

go version # should now print `go version go1.21.4 linux/amd64`.
```

## Run

With the setup complete, run the following commands to start and test the system (see the `utils` directory).

```sh
cd utils
./start_master.sh # run the master
./start_worker.sh <number_of_workers> <ip_address_of_master> # run a number of workers
./spawn_small_job.sh <ip_address_of_master> # spawn a job
```
