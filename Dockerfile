# Use Python 3.11 full image (not slim) to get python3-dev and build tools
# needed for compiling RPi.GPIO and spidev native extensions for GPIO access
FROM python:3.11

WORKDIR /app

# Note: Standard python:3.11 image already includes all image processing libraries
# (libjpeg-dev, zlib1g-dev, libfreetype-dev, liblcms2-dev, libopenjp2-7-dev)
# and build tools (gcc, python3-dev) so no additional packages needed!

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the application source code
COPY src/ src/
COPY lib/ lib/
COPY cli.py .

# Copy entrypoint script
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

# Create directories that will be volume mounted or used at runtime
RUN mkdir -p pic pic-raw logs config

ENV FLASK_APP=src/main.py
ENV FLASK_ENV=development
ENV PYTHONPATH=/app

EXPOSE 5000

CMD ["./docker-entrypoint.sh"]
