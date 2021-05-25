# Provides a list of available Hetzner Cloud Datacenters:
# https://registry.terraform.io/providers/hetznercloud/hcloud/latest/docs/data-sources/datacenters

data "hcloud_datacenters" "ds" {
}

resource "local_file" "datacenters" {
  content = jsonencode({
    "datacenters" = {
      "ids" = data.hcloud_datacenters.ds.datacenter_ids,
      "names" = data.hcloud_datacenters.ds.names,
      "descriptions" = data.hcloud_datacenters.ds.descriptions,
    }
  })

  filename = "${var.outputs_dir}/hcloud/datacenters.json"

  depends_on = [
    data.hcloud_datacenters.ds,
  ]
}

# Provides a list of available Hetzner Cloud Locations:
# https://registry.terraform.io/providers/hetznercloud/hcloud/latest/docs/data-sources/locations

data "hcloud_locations" "ds" {
}

resource "local_file" "locations" {
  content = jsonencode({
    "locations" = {
      "ids" = data.hcloud_locations.ds.location_ids,
      "names" = data.hcloud_locations.ds.names,
      "descriptions" = data.hcloud_locations.ds.descriptions,
    }
  })

  filename = "${var.outputs_dir}/hcloud/locations.json"

  depends_on = [
    data.hcloud_locations.ds,
  ]
}

# Provides a list of available Hetzner Cloud Server Types:
# https://registry.terraform.io/providers/hetznercloud/hcloud/latest/docs/data-sources/server_types

data "hcloud_server_types" "ds" {
}

resource "local_file" "server_types" {
  content = jsonencode({
    "server_types" = {
      "ids" = data.hcloud_server_types.ds.server_type_ids,
      "names" = data.hcloud_server_types.ds.names,
      "descriptions" = data.hcloud_server_types.ds.descriptions,
    }
  })

  filename = "${var.outputs_dir}/hcloud/server_types.json"

  depends_on = [
    data.hcloud_server_types.ds,
  ]
}

# Provides details about Hetzner Cloud SSH Keys, useful if you want to use a non-terraform managed SSH Key:
# https://registry.terraform.io/providers/hetznercloud/hcloud/latest/docs/data-sources/ssh_keys

data "hcloud_ssh_keys" "superusers" {
  # You have to upload your SSH public keys to the Hetzner Cloud project using the web UI:
  # after the upload is completed tag them with the key "superuser" and value "true"
  with_selector = "superuser=true"
}
