```bash
ansible-galaxy collection install community.kubernetes
ansible-galaxy collection install hetzner.hcloud

ansible-playbook create-hcloud-infrastructure.yaml  -e "state=present"
ansible-playbook create-kubernetes-cluster.yaml -i env/inventory --private-key ~/.ssh/talexdev_rsa
ansible-playbook deploy-db-prometheus.yaml
ansible-playbook deploy-db-pg.yaml
ansible-playbook deploy-app-termine.yaml
ansible-playbook deploy-ingress.yaml
```

install: htpasswd, openssl
