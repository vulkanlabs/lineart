
# Testing
.PHONY: test
test:
	uv run pytest -sv --tb=short --disable-warnings -m "not integration"

.PHONY: test-integration
test-integration:
	uv run pytest -sv --tb=short --disable-warnings -m "integration"

# Development & Deployment
.PHONY: lint
lint: lint-python
	cd frontend && npm run format
	
.PHONY: lint-python
lint-python:
	uv run ruff check --force-exclude --select I --fix
	uv run ruff format --force-exclude
	uv run ruff check --force-exclude --extend-ignore="F401" .

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
	cd frontend/packages/client-open && npm run build

# Configuration
.PHONY: config
config:
	mv ./config/active ./config/active.bkp || true
	cp -r ./config/local ./config/active
	cp ./config/active/.env ./.env
	cp ./config/active/.env ./frontend/apps/open/.env

# Maintenance
.PHONY: clean-pycache
clean-pycache:
	 find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

.PHONY: speakeasy
speakeasy: clean-pycache openapi
	cd sdks/python && speakeasy run --skip-versioning
