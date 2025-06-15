SCHEMAS_DIR:= schemas
YAML_DIR:= controller

.PHONY: validate-schemas lint ansible-lint ci-checks

validate-schemas:
	check-jsonschema --schemafile $(SCHEMAS_DIR)/hosts.schema.json $(YAML_DIR)/hosts.yml
	check-jsonschema --schemafile $(SCHEMAS_DIR)/inventory.schema.json $(YAML_DIR)/inventory.yml
	check-jsonschema --schemafile $(SCHEMAS_DIR)/job_templates.schema.json $(YAML_DIR)/job_templates.yml
	check-jsonschema --schemafile $(SCHEMAS_DIR)/projects.schema.json $(YAML_DIR)/projects.yml

lint: ansible-lint
ansible-lint:
	ansible-lint -p -v --exclude .git --exclude .tox --exclude .venv --exclude .mypy_cache --exclude .pytest_cache --exclude .idea --exclude .vscode $(YAML_DIR)/*.yml

ci-checks:
	python scripts/ci_check.py
