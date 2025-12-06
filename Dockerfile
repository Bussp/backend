FROM python:3.12-alpine
WORKDIR /code
ENV FAST_APP=src/
ENV FAST_RUN_HOST=0.0.0.0
RUN apk add --no-cache gcc musl-dev linux-headers
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
EXPOSE 8000
COPY . .
CMD ["python3.12", "-m", "src.main"]