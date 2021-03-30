install: install-minikube install-monitoring install-databases install-app install-ingress

use-context:
	 kubectl config use-context minikube

install-minikube:
	ansible-playbook deploy-minikube-start.yaml

install-databases: use-context
	ansible-playbook deploy-db-pg.yaml
	ansible-playbook deploy-db-ldap.yaml

install-ingress: use-context
	ansible-playbook deploy-ingress.yaml
	ansible-playbook deploy-hosts.yaml --ask-become-pass

install-monitoring: use-context
	ansible-playbook deploy-prometheus.yaml

install-app:
	ansible-playbook deploy-app-termine.yaml

uninstall:
	ansible-playbook deploy-minikube-delete.yaml

reinstall: uninstall install
