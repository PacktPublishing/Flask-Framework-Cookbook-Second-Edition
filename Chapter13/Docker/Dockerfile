FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT [ "python" ]
CMD [ "run.py" ]
