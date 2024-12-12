.PHONY: down
down:
	rm -r ./dist/ || true
	docker-compose down -v --remove-orphans

.PHONY: build
build:
	uv build --wheel --all
	docker-compose build

.PHONY: up
up:
	docker-compose up

# Code generation for frontend types
.PHONY: openapi
openapi:
	uv run python scripts/export-openapi.py --out generated/openapi.json
	rm -r frontend/generated || true
	openapi-generator-cli generate -g typescript-fetch -i generated/openapi.json -o frontend/generated --additional-properties="modelPropertyNaming=original"

# Configuration
.PHONY: config
config:
	uv run python scripts/config-manager.py

.PHONY: pull-config
pull-config:
	gcloud storage cp -r gs://vulkan-bootstrap-env-config/config . 

# Maintenance
.PHONY: clean-pycache
clean-pycache:
	 find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete
