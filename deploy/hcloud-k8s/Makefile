install: install-ansible-dependencies install-hcloud-servers install-k8s-cluster

install-ansible-dependencies:
	ansible-galaxy collection install community.kubernetes
	ansible-galaxy collection install hetzner.hcloud

install-hcloud-servers:
	ansible-playbook create-hcloud-infrastructure.yaml  -e "state=present"
	sleep 300

install-k8s-cluster:
	ansible-playbook create-kubernetes-cluster.yaml -i env/inventory --private-key ~/.ssh/talexdev_rsa
	ansible-playbook deploy-db-prometheus.yaml
	ansible-playbook deploy-db-pg.yaml
	ansible-playbook deploy-app-termine.yaml
	ansible-playbook deploy-ingress.yaml
