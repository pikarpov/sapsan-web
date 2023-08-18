FROM python:3.10-slim

ENV GIT_PYTHON_REFRESH=quiet

# copy into a directory of its own (so it isn't in the toplevel dir)
COPY . /app
WORKDIR /app

RUN apt-get update
RUN pip install -U pip
RUN pip install sapsan
RUN pip install torch==1.13
RUN apt-get install ffmpeg libsm6 libxext6  -y

# remember to expose the port your app'll be exposed on.
EXPOSE 8080

# run it!
ENTRYPOINT ["streamlit", "run", "Welcome.py", "--server.port=8080", "--server.address=0.0.0.0"]
