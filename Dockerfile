FROM debian:bullseye

WORKDIR /usr/src/app
COPY requirements.txt .
RUN apt-get update
RUN apt-get install -y python3 python3-pip python3-dev libffi-dev ffmpeg
RUN pip install -r ./requirements.txt
COPY . .

CMD ["python3", "./radio_neko_streaming.py"]
