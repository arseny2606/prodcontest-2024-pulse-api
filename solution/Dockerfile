FROM python:3.12.1

WORKDIR /app

RUN apt install gcc
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

ENV SERVER_PORT=8080
ENV JWT_SECRET_KEY="4178f676259dcb57a569c2c725b3d94183ef4cf7452886be0c4f765118af9450"

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $SERVER_PORT"]