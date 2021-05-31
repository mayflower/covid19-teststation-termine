# Provides a Hetzner Cloud SSH key resource to manage SSH keys for server access:
# https://registry.terraform.io/providers/hetznercloud/hcloud/latest/docs/resources/ssh_key

resource "hcloud_ssh_key" "default" {
  name = "SSH Key"
  public_key = var.ssh_key
}
