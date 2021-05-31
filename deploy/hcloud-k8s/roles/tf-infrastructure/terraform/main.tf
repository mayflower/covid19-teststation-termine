terraform {
  required_version = ">= 0.14.7"

  required_providers {
    hcloud = {
      source = "hetznercloud/hcloud"
      version = "1.25.2"
    }

    hetznerdns = {
      source = "timohirt/hetznerdns"
      version = "1.1.1"
    }
  }
}

provider "hcloud" {
  token = var.hcloud_token
}

provider "hetznerdns" {
  apitoken = var.dns_token
}
