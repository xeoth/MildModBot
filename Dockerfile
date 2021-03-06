FROM python:3.8.8-slim

WORKDIR /bot

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY . .

CMD ["python", "src/index.py"]