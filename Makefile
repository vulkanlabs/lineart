.PHONY: init_db
init_db:
	rm server/example.db
	poetry run python server/db.py

.PHONY: images
images:
	docker-compose build --no-cache