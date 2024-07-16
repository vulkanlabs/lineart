.PHONY: init_db
init_db:
	rm server/example.db
	poetry run python server/db.py