# Provides details about a Hetzner DNS Zone:
# https://registry.terraform.io/providers/timohirt/hetznerdns/latest/docs/data-sources/hetznerdns_zone

data "hetznerdns_zone" "cluster" {
  # Provides details about a Hetzner DNS Zone with the given name that already exists
  name = var.domain
}

# Provides a Hetzner DNS Record resource to create, update and delete DNS Records:
# https://registry.terraform.io/providers/timohirt/hetznerdns/latest/docs/resources/hetznerdns_record

# Create CNAME record for the master node, control plane with single master node setup
#
resource "hetznerdns_record" "api-single-master" {
  count = var.use_single_master

  # Id of the DNS zone to create the record in
  zone_id = data.hetznerdns_zone.cluster.id

  # Name of the DNS record to create
  name = "${var.control_plane_host}.${var.subdomain}"

  # The value of the record (eg. 192.168.1.1),
  # for TXT records with quoted values the quotes have to be escaped in Terraform
  value = hcloud_rdns.rdns_master[count.index].dns_ptr

  # The type of the record
  type = "CNAME"

  # Time to live of this record
  ttl = var.dns_ttl
}
