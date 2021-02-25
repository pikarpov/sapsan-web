FROM python:3.8.5-slim

# remember to expose the port your app'll be exposed on.
EXPOSE 8080

ENV GIT_PYTHON_REFRESH=quiet
RUN pip install -U pip

#COPY requirements.txt app/requirements.txt
RUN pip install sapsan

# copy into a directory of its own (so it isn't in the toplevel dir)
COPY . /app
WORKDIR /app

# run it!
ENTRYPOINT ["streamlit", "run", "st_intro.py", "--server.port=8080", "--server.address=0.0.0.0"]
