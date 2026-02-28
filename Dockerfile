FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dev tools
RUN pip install ipython django-extensions

# Copy project
COPY . .

# Expose port
EXPOSE 8000

# Keep container running with root access for dev
CMD ["tail", "-f", "/dev/null"]
