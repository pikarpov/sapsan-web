.PHONY: run run-container gcloud-deploy

run:
	@streamlit run Welcome.py --server.port=8080 --server.address=localhost

build-container:
	@docker build . -t sapsan-web

run-container:	
	@docker run -p 8080:8080 sapsan-web

# gcloud-deploy:
# 	@gcloud app deploy app.yaml
