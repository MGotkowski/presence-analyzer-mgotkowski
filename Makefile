run:
	docker-compose up
run-dev:
	docker-compose --file docker-compose-dev.yml run --service-ports web
