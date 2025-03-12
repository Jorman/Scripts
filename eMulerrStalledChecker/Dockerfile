FROM python:3.11-alpine

WORKDIR /app
COPY requirements.txt .
COPY eMulerr_Stalled_Checker.py .

RUN pip install -r requirements.txt

CMD ["python", "eMulerr_Stalled_Checker.py"]