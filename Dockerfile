# Use a specific slim Python image for a smaller footprint
FROM python:3.11-slim

# Set environment variables to prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install LibreOffice and other necessary system dependencies
# Running apt-get update and install in the same RUN command to reduce layers
# and ensure the package list is up-to-date for the install.
RUN apt-get update && \
    apt-get install -y --no-install-recommends libreoffice wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user and group for security
RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid 1001 -m -s /bin/bash appuser

# Set the working directory
WORKDIR /app

# Install uv, the Python package installer
RUN pip install uv

# Copy only the dependency definition file first to leverage Docker's build cache
COPY pyproject.toml /app/

# Install Python dependencies using uv
# This installs dependencies into the system's Python, which is fine for the container
RUN uv pip install --system .

# Copy the rest of the application source code
COPY ./src /app/src

# Change ownership of the app directory to the non-root user
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using uvicorn
# The --host 0.0.0.0 makes the server accessible from outside the container
CMD ["uvicorn", "docling_lib.server:app", "--host", "0.0.0.0", "--port", "8000"]
