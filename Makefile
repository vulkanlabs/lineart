
# Testing
.PHONY: test
test:
	uv run pytest -sv --tb=short --disable-warnings -m "not integration"

.PHONY: test-integration
test-integration:
	uv run pytest -sv --tb=short --disable-warnings -m "integration"

# Development & Deployment
.PHONY: lint
lint:
	cd frontend && npm run format

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

.PHONY: run
run: config
	docker-compose up -d

# Code generation for frontend types
.PHONY: openapi
openapi:
	uv run python scripts/export-openapi.py --out generated/openapi.json
	rm -r frontend/packages/client-open/src || true
	mkdir -p frontend/packages/client-open/src
	openapi-generator-cli generate -g typescript-fetch -i generated/openapi.json -o frontend/packages/client-open/src --additional-properties="modelPropertyNaming=original"

# Configuration
.PHONY: config
config:
	cp -r ./config/local ./config/active
	cp ./config/active/.env ./.env
	cp ./config/active/.env ./frontend/apps/open/.env

# Maintenance
.PHONY: clean-pycache
clean-pycache:
	 find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete
