output "master_ipv4" {
  description = "Public IPv4 addresses of all master nodes"

  value = [
    hcloud_server.master-node.*.ipv4_address,
  ]
}

output "master_ipv4_private" {
  description = "Private IPv4 addresses of all master nodes"

  value = [
    hcloud_server_network.master.*.ip,
  ]
}

output "worker_ipv4" {
  description = "Public IPv4 addresses of all worker nodes"

  value = [
    hcloud_server.worker-node.*.ipv4_address,
  ]
}

output "worker_ipv4_private" {
  description = "Private IPv4 addresses of all worker nodes"

  value = [
    hcloud_server_network.worker.*.ip,
  ]
}
