.PHONY: clean
clean:
	docker-compose down --volumes --remove-orphans
	
.PHONY: images
images:
	docker-compose build --no-cache