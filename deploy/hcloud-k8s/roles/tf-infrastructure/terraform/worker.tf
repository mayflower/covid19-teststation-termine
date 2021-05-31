# Provides an Hetzner Cloud server resource. This can be used to create, modify, and delete servers:
# https://registry.terraform.io/providers/hetznercloud/hcloud/latest/docs/resources/server

resource "hcloud_server" "worker-node" {
  # Create a new Hetzner Cloud Server for each k8s worker node
  count = var.worker_count

  # Name of the server to create (must be unique per project and a valid hostname as per RFC 1123)
  name = "worker${count.index + 1}"

  # The datacenter name to create the server in,
  # see hcloud_datacenters TF data source for a listing of all available data centers
  location = var.datacenter

  # Name or ID of the image the server is created from
  image = var.os_image

  # Name of the server type this server should be created with,
  # see hcloud_server_types TF data source for a listing of all available server types
  server_type = var.worker_server_type

  # Cloud-Init user data to use during server creation, see https://community.hetzner.com/tutorials/basic-cloud-config
  user_data = file("./user-data/cloud-config.worker.yaml")

  # SSH key IDs or names which should be injected into the server at creation time
  ssh_keys = [ hcloud_ssh_key.default.id ]

  depends_on = [
    hcloud_network.k8s-cluster-network,
    hcloud_network_subnet.k8s-worker-nodes-subnet,
    hcloud_ssh_key.default,
  ]

  labels = {
    "node-role" = "worker",
    "cluster-name" = var.cluster_name,
    "builder" = "terraform",
  }
}

# Provides a Hetzner Cloud Server Network to represent a private network on a server in the Hetzner Cloud:
# https://registry.terraform.io/providers/hetznercloud/hcloud/latest/docs/resources/server_network

resource "hcloud_server_network" "worker" {
  # Connect each Hetzner Cloud Server to the its private network for worker nodes
  count = length(hcloud_server.worker-node)

  # ID of the server
  server_id = hcloud_server.worker-node[count.index].id

  # ID of the sub-network which should be added to the server
  subnet_id = hcloud_network_subnet.k8s-worker-nodes-subnet.id

  # Set an IP address from the pool of worker nodes
  ip = "${var.subnet_worker_ip}.${count.index + var.subnet_all_offset}"
}

# Provides a Hetzner Cloud Reverse DNS Entry to create, modify and reset reverse dns entries for Hetzner Cloud Floating IPs or servers:
# https://registry.terraform.io/providers/hetznercloud/hcloud/latest/docs/resources/rdns

resource "hcloud_rdns" "rdns_worker" {
  # Create a reverse DNS entry for each k8s worker node
  count = length(hcloud_server.worker-node)

  # The server the ip_address belongs to
  server_id = hcloud_server.worker-node[count.index].id

  # The IP address that should point to dns_ptr
  ip_address = hcloud_server.worker-node[count.index].ipv4_address

  # The DNS address the ip_address should resolve to
  dns_ptr = "${hcloud_server.worker-node[count.index].name}.${var.subdomain}.${var.domain}"
}

# Provides a Hetzner DNS Record resource to create, update and delete DNS Records:
# https://registry.terraform.io/providers/timohirt/hetznerdns/latest/docs/resources/hetznerdns_record

resource "hetznerdns_record" "worker" {
  # Create a DNS entry for each k8s worker node
  count = var.worker_count

  # Id of the DNS zone to create the record in
  zone_id = data.hetznerdns_zone.cluster.id

  # Name of the DNS record to create
  name = replace(hcloud_rdns.rdns_worker[count.index].dns_ptr, ".${var.domain}", "")

  # The value of the record (eg. 192.168.1.1),
  # for TXT records with quoted values the quotes have to be escaped in Terraform
  value = hcloud_rdns.rdns_worker[count.index].ip_address

  # The type of the record
  type = "A"

  # Time to live of this record
  ttl = var.dns_ttl
}
