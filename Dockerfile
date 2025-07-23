# ✅ Base Python image
FROM python:3.10-slim

# ✅ Prevent unnecessary pyc files, better logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ✅ Install Git
RUN apt update && apt install -y git && apt clean && rm -rf /var/lib/apt/lists/*

# ✅ Set working directory
WORKDIR /app

# ✅ Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -U pip && pip install --no-cache-dir -r requirements.txt

# ✅ Copy entire bot code
COPY . .

# ✅ Run the bot — assumes your main file is bot.py
CMD ["python", "bot.py"]
