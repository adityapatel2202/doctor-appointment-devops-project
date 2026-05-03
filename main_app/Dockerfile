FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt . 
# Copy the requirements file to the working directory

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]