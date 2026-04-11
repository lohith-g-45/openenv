FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

# Run inference.py first so the validator can read [TASK] scoring output,
# then start the FastAPI server.
CMD ["sh", "-c", "python inference.py && python -m server.app"]

