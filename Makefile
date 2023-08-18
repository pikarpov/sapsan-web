.PHONY: run run-container gcloud-deploy

run:
	@streamlit run Welcome.py --server.port=8080 --server.address=localhost

run-container:
	@docker build . -t sapsan-web
	@docker run -p 8080:8080 sapsan-web

# rpi-deploy:

# gcloud-deploy:
# 	@gcloud app deploy app.yaml
