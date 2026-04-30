# FishTank

> A containerized Android OTA testing platform built on Cuttlefish, raikou-net, and Docker, designed to simulate real-world update and network scenarios on physical servers, developer workstations, or virtualised environments with minimal host configuration.

---

## Overview

**FishTank** is an integrated testing environment for Android Over-The-Air (OTA) updates and network configuration validation. It combines:

- **Google's Cuttlefish** AOSP Android emulator
- A dedicated **OTA update server** for distributing and validating system images
- **[raikou-net](https://github.com/lgirdk/raikou-net)** for container network orchestration and LAN infrastructure simulation
- **SSH access** for remote management and debugging
- **Physical interface passthrough** via USB tethering, supporting bare-metal servers, developer workstations, and virtualised environments (e.g. VirtualBox)

The name reflects the Cuttlefish emulator living inside a controlled container ecosystem - a tank where every variable is observable and testable.

---

## Use Cases

### Repeatable, Isolated Test Environments

Every `docker compose up` produces an identical, clean-slate environment regardless of host state. There is no residual configuration, no leftover update state, and no dependency on a shared physical device. Teams working across different machines or running tests in parallel get consistent results because the entire stack is defined in code.

### Fast Setup and Teardown

Spinning up a full Android OTA test environment takes a single command. Tearing it down is equally instant. This makes FishTank well suited for short-lived test runs in CI pipelines, ad-hoc debugging sessions, or situations where you need to rapidly test against multiple build variants without maintaining separate long-lived device labs.

### OTA Build Validation Before Release

Before promoting an OTA package to a physical device fleet, FishTank lets you validate the full update flow which includes package serving, device download, apply, and reboot in an emulated environment. This catches infrastructure and packaging issues early, without risking real hardware or requiring a device lab to be available.

### Android Build and Release Engineering

FishTank maps directly to build and release workflows: you point the OTA server at a newly built system image, trigger the update on Cuttlefish, and verify the resulting system state via ADB. This is useful for testing incremental OTAs, full image replacements, and rollback scenarios across different AOSP branches and build targets.

### Network Scenario Testing

Using raikou-net's `config.json`-driven network primitives, you can simulate different LAN topologies, VLAN configurations, and routing scenarios without touching host networking. Scenarios are version-controlled alongside the rest of the platform, making them reproducible and reviewable.

### Local Development Without a Device Lab

For engineers who don't have access to a physical Android device lab, FishTank provides a self-contained alternative that runs on a laptop or workstation. The USB tethering interface passthrough means it can also integrate with real network hardware when needed, bridging the gap between pure emulation and physical testing.

### CI/CD Integration

Because the entire platform is based on `docker compose`, it can be incorporated into any CI system that supports Docker. A pipeline can bring up FishTank, push an OTA package, run validation steps via ADB, and tear everything down, all within a single job, with no persistent state between runs.

---

## Architecture

FishTank currently consists of five interconnected services:

| Service | Role |
| --- | --- |
| `cuttlefish` | AOSP Android emulator (x86\_64 or ARM64) |
| `ota-server` | Update package distribution and management |
| `orchestrator` | Network bridge and container orchestration via raikou-net |
| `ota-base` | Shared base image for OTA infrastructure |
| `ssh-service` | Secure access and management interface |

### Network Topology

Inter-container communication runs over a custom bridge network `cuttlefish-ota`:

```sh
Host (Physical Server / VM / Workstation)
└── USB Tethered / Physical Interface (e.g. enxc6f63813d463)
    └── Bridge: cuttlefish-ota (10.106.185.0/24)
        ├── OTA Server:   10.106.185.201/24
        ├── Cuttlefish:   10.106.185.202/24
        └── Gateway:      10.106.185.31
```

---

## Host Setup

FishTank is host-agnostic, it runs equally well on **bare-metal servers**, **developer workstations**, and **virtualised environments** (VirtualBox, VMware, KVM guests, cloud VMs). The only requirements are Docker, KVM access, and a network interface to use as the bridge parent.

### Physical Server or Workstation

This is the simplest setup. Any Linux machine with KVM support works out of the box.

1. **Identify your network interface**

   ```bash
   ip link show
   ```

   This could be a built-in NIC (`eth0`, `enp0s3`), a USB Ethernet adapter, or a phone/device in USB tethering mode. The interface name maps to `parent` in `config.json`.

2. **Verify KVM availability**

   ```bash
   lsmod | grep kvm
   ls -l /dev/kvm
   ```

   On most modern Linux distributions with a desktop or server kernel, KVM is available without additional configuration.

3. **Update `config.json`** with your interface name and proceed to [Getting Started](#getting-started).

### VirtualBox (Developer Workstation)

When running FishTank inside a VirtualBox VM, USB tethering is a practical way to pass a physical interface into the guest without complex bridged adapter configuration.

1. **Attach the USB device to the VM**

   In VirtualBox Manager → *Settings → USB*, add a USB filter for your tethered device (e.g. a phone in USB tethering mode or a USB Ethernet adapter). Set the USB controller to USB 3.0 (xHCI) for reliable passthrough.

2. **Enable nested virtualisation** (required for KVM inside the guest):

   ```bash
   # Run on the host, with the VM powered off
   VBoxManage modifyvm "YourVMName" --nested-hw-virt on
   ```

3. **Verify KVM and the interface inside the VM**

   ```bash
   lsmod | grep kvm
   ip link show   # Note the USB-tethered interface name, e.g. enxc6f63813d463
   ```

4. **Update `config.json`** with the interface name from the guest VM.

### Other Hypervisors / Cloud VMs

- **VMware / Hyper-V**: Enable nested virtualisation in VM settings and attach a USB or virtual NIC as the bridge parent.
- **Cloud VMs (AWS, GCP, Azure)**: Nested KVM is supported on most modern instance types (`metal` on AWS, `n2` on GCP). Use a secondary vNIC as the bridge parent rather than USB tethering.
- **KVM guests**: Enable nested virtualisation with `cpu host` passthrough in the VM XML config.

In all cases the only thing that changes is the `parent` interface name in `config.json`. Everything else is identical.

---

## raikou-net Integration

FishTank uses **[raikou-net](https://github.com/lgirdk/raikou-net)** as its network orchestration backbone. raikou-net provides:

- **Bridge creation and management** between containers and physical/virtual interfaces
- **LAN infrastructure simulation** (DHCP, routing, VLAN support)
- **Extensible network scenarios** via `config.json` without rebuilding containers

The `orchestrator` service pulls from raikou-net and is responsible for configuring the `cuttlefish-ota` bridge at startup, wiring the USB-tethered physical interface as the upstream parent, and providing host network access to all downstream containers.

The SSH service component is maintained at [github.com/lgirdk/raikou-net](https://github.com/lgirdk/raikou-net).

---

## Project Structure

```sh
fishtank/
├── docker-compose.yml          # Service definitions and resource limits
├── config.json                 # Network bridge and interface configuration
├── components/
│   ├── cuttlefish/
│   │   ├── Dockerfile
│   │   └── entrypoint.sh
│   └── ota-server/
│       └── Dockerfile
└── README.md
```

---

## Prerequisites

- Linux host — bare-metal server, workstation, or VM (VirtualBox, VMware, KVM, cloud)
  - Docker and Docker Compose
  - KVM support (`/dev/kvm` accessible; for VMs, nested virtualisation must be enabled)
  - A network interface to use as the bridge parent — a physical NIC, USB Ethernet adapter, or USB-tethered device
  - Minimum **10 GB RAM** available to the host (Cuttlefish alone requires 10 GB)
- Root or sudo privileges for privileged container operations

---

## Configuration

### Network Configuration (`config.json`)

```json
{
  "bridge": "cuttlefish-ota",
  "subnet": "10.106.185.0/24",
  "gateway": "10.106.185.31",
  "parent": "enxc6f63813d463"
}
```

Update `parent` to match your USB-tethered interface name.

### Cuttlefish Build Arguments

| Argument | Default | Description |
|---|---|---|
| `BUILD_ID` | `15067704` | AOSP build identifier |
| `ARCH` | `x86_64` | Target architecture (`x86_64` or `arm64`) |
| `BRANCH` | `aosp-android13-gsi` | AOSP branch |
| `TARGET_x86_64` | `aosp_cf_x86_64_only_phone-userdebug` | x86\_64 build target |
| `TARGET_arm64` | `aosp_cf_arm64_only_phone-userdebug` | ARM64 build target |

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `NW_CONFIG` | — | Path to `config.json` on the host (mounted to `/root/config.json` in orchestrator) |
| `LEGACY` | `no` | OTA server legacy mode flag |

---

## Getting Started

### 1. Clone and configure

```bash
git clone https://github.com/your-org/fishtank.git
cd fishtank
# Edit config.json to set the correct parent interface
```

### 2. Build images

```bash
docker compose build
```

### 3. Start services

```bash
docker compose up -d
```

### 4. Access services

| Service | Access |
|---|---|
| Cuttlefish VNC | `localhost:5900` (VNC viewer required) |
| Cuttlefish ADB | `localhost:6520` |
| OTA Server | `10.106.185.201` |
| SSH | Via orchestrator |

### 5. Stop services

```bash
docker compose down
```

---

## Testing Workflows

### OTA Update Testing

1. Start FishTank with `docker compose up`
2. Connect to Cuttlefish via VNC (`localhost:5900`)
3. Place an update package on the OTA server (`10.106.185.201`)
4. Trigger the update from the emulated device
5. Verify update completion and system state via ADB

### Network Configuration Testing

1. Modify `config.json` to define custom network scenarios (VLANs, alternate subnets)
2. Rebuild the orchestrator: `docker compose up -d --build orchestrator`
3. Validate inter-container connectivity
4. Test VLAN translation and failover scenarios using raikou-net's network primitives

---

## Resource Limits

| Resource | Limit |
|---|---|
| Cuttlefish memory | 10 GB (swap disabled) |
| Devices | KVM, TAP, vhost, GPU |
| Capabilities | `NET_ADMIN`, `NET_RAW`, `SYS_ADMIN`, `SYS_PTRACE`, `MKNOD` |

Seccomp is disabled for the Cuttlefish container to support full emulation capabilities.

---

## Troubleshooting

### KVM not available

On a physical host, ensure the kernel module is loaded:

```bash
lsmod | grep kvm
modprobe kvm_intel   # or kvm_amd
```

On VirtualBox, enable nested virtualisation on the host first (VM must be powered off):

```bash
VBoxManage modifyvm "YourVMName" --nested-hw-virt on
```

On cloud VMs, verify the instance type supports nested KVM (e.g. AWS `metal`, GCP `n2`).

### Network interface not appearing

On a physical host, verify the interface is up:

```bash
ip link show
dmesg | grep -i usb   # for USB-tethered devices
```

On VirtualBox, check the USB device is correctly filtered and attached in VM USB settings. Ensure the interface name in `config.json` matches what the host assigned.

### Network bridge not coming up

Verify raikou-net's orchestrator has the correct interface name and that the container has `NET_ADMIN` capability. Check orchestrator logs:

```bash
docker compose logs orchestrator
```

### Container memory issues

Check available system memory and adjust the Cuttlefish memory limit in `docker-compose.yml`:

```bash
free -h
```

---

## Security Considerations

- Containers run with elevated privileges for hardware access and network management
- Seccomp profiles are disabled for Cuttlefish
- Restrict host network and Docker socket access in production environments
- Consider adding network policies and SELinux/AppArmor rules around the bridge interface

---

## Dependencies

| Dependency | Source |
| --- | --- |
| raikou-net (orchestrator) | [github.com/lgirdk/raikou-net](https://github.com/lgirdk/raikou-net) |
| SSH service | [github.com/lgirdk/raikou-net](https://github.com/lgirdk/raikou-net) |
| Cuttlefish | [Android Cuttlefish documentation](https://source.android.com/docs/setup/create/cuttlefish) |

---

## License

Refer to individual component licenses from upstream repositories (AOSP, raikou-net).
