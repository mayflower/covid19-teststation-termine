# Provides an Hetzner Cloud server resource. This can be used to create, modify, and delete servers:
# https://registry.terraform.io/providers/hetznercloud/hcloud/latest/docs/resources/server

resource "hcloud_server" "master-node" {
  # Create a new Hetzner Cloud Server for each k8s master node
  count = var.master_count

  # Name of the server to create (must be unique per project and a valid hostname as per RFC 1123)
  name = "master${count.index + 1}"

  # The datacenter name to create the server in,
  # see hcloud_datacenters TF data source for a listing of all available data centers
  location = var.datacenter

  # Name or ID of the image the server is created from
  image = var.os_image

  # Name of the server type this server should be created with,
  # see hcloud_server_types TF data source for a listing of all available server types
  server_type = var.master_server_type

  # Cloud-Init user data to use during server creation, see https://community.hetzner.com/tutorials/basic-cloud-config
  user_data = file("./user-data/cloud-config.master.yaml")

  # SSH key IDs or names which should be injected into the server at creation time
  ssh_keys = data.hcloud_ssh_keys.superusers.ssh_keys.*.id

  labels = {
    "node-role" = "master",
    "cluster-name" = var.cluster_name,
    "builder" = "terraform",
  }
}

# Provides a Hetzner Cloud Server Network to represent a private network on a server in the Hetzner Cloud:
# https://registry.terraform.io/providers/hetznercloud/hcloud/latest/docs/resources/server_network

resource "hcloud_server_network" "master" {
  # Connect each Hetzner Cloud Server to the its private network for master nodes
  count = length(hcloud_server.master-node)

  # ID of the server
  server_id = hcloud_server.master-node[count.index].id

  # ID of the sub-network which should be added to the server
  subnet_id = hcloud_network_subnet.k8s-master-nodes-subnet.id

  # Set an IP address from the pool of master nodes
  ip = "${var.subnet_master_ip}.${count.index + var.subnet_all_offset}"
}

# Provides a Hetzner Cloud Reverse DNS Entry to create, modify and reset reverse dns entries for Hetzner Cloud Floating IPs or servers:
# https://registry.terraform.io/providers/hetznercloud/hcloud/latest/docs/resources/rdns

resource "hcloud_rdns" "rdns_master" {
  # Create a reverse DNS entry for each k8s master node
  count = length(hcloud_server.master-node)

  # The server the ip_address belongs to
  server_id = hcloud_server.master-node[count.index].id

  # The IP address that should point to dns_ptr
  ip_address = hcloud_server.master-node[count.index].ipv4_address

  # The DNS address the ip_address should resolve to
  dns_ptr = "${hcloud_server.master-node[count.index].name}.${var.subdomain}.${var.domain}"
}

# Provides a Hetzner DNS Record resource to create, update and delete DNS Records:
# https://registry.terraform.io/providers/timohirt/hetznerdns/latest/docs/resources/hetznerdns_record

resource "hetznerdns_record" "master" {
  # Create a DNS entry for each k8s master node
  count = var.master_count

  # Id of the DNS zone to create the record in
  zone_id = data.hetznerdns_zone.cluster.id

  # Name of the DNS record to create
  name = replace(hcloud_rdns.rdns_master[count.index].dns_ptr, ".${var.domain}", "")

  # The value of the record (eg. 192.168.1.1),
  # for TXT records with quoted values the quotes have to be escaped in Terraform
  value = hcloud_rdns.rdns_master[count.index].ip_address

  # The type of the record
  type = "A"

  # Time to live of this record
  ttl = var.dns_ttl
}
