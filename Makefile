.PHONY: run run-container gcloud-deploy

run:
	@streamlit run st_intro.py --server.port=8080 --server.address=0.0.0.0

run-container:
	@docker build . -t sapsan-web
	@docker run -p 8080:8080 sapsan-web

gcloud-deploy:
	@gcloud app deploy app.yaml
