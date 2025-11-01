FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && pip install pre-commit
COPY . .
CMD ["python", "-m", "src.run", "--projects", "HADOOP", "KAFKA", "SPARK", "--since", "2018-01-01", "--out", "output"]
