.PHONY: clean-pycache
clean-pycache:
	 find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

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
