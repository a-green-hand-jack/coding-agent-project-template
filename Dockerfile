# Replace the base image, runtime command and dependency policy for the product.
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml ./
COPY src/ ./src/

RUN python -m pip install --no-cache-dir .

# Replace this placeholder with the product's public entrypoint.
CMD ["python", "-c", "print('replace Dockerfile CMD with the product entrypoint')"]
