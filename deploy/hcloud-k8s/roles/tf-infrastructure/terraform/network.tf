# Provides a Hetzner Cloud Network to represent a network in the Hetzner Cloud:
# https://registry.terraform.io/providers/hetznercloud/hcloud/latest/docs/resources/network

resource "hcloud_network" "k8s-cluster-network" {
  # Name of the network to create (must be unique per project)
  name = "kubernetes"

  # IP Range of the whole network which must span all included subnets and route destinations,
  # must be one of the private ipv4 ranges of RFC1918
  ip_range = var.network_ip_range

  labels = {
    "cluster-name" = var.cluster_name,
    "builder" = "terraform",
  }
}

# Provides a Hetzner Cloud Network Subnet to represent a subnet in the Hetzner Cloud:
# https://registry.terraform.io/providers/hetznercloud/hcloud/latest/docs/resources/network_subnet

resource "hcloud_network_subnet" "k8s-master-nodes-subnet" {
  # ID of the network the subnet should be added to
  network_id = hcloud_network.k8s-cluster-network.id

  # Type of subnet: server, cloud or vswitch (server option is deprecated, use cloud instead)
  type = "cloud"

  # Name of network zone
  network_zone = var.network_zone

  # Range to allocate IPs from, must be a subnet of the ip_range of the network
  # and must not overlap with any other subnets or with any destinations in routes
  ip_range = var.subnet_master_ip_range
}

resource "hcloud_network_subnet" "k8s-worker-nodes-subnet" {
  # ID of the network the subnet should be added to
  network_id = hcloud_network.k8s-cluster-network.id

  # Type of subnet: server, cloud or vswitch (server option is deprecated, use cloud instead)
  type = "cloud"

  # Name of network zone
  network_zone = var.network_zone

  # Range to allocate IPs from, must be a subnet of the ip_range of the network
  # and must not overlap with any other subnets or with any destinations in routes
  ip_range = var.subnet_worker_ip_range
}
