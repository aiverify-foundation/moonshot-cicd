# Use the official Python base image for building
FROM python:3.12-slim-bookworm AS build

RUN apt-get update && apt-get -y upgrade && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the requirements file and README.md into the container
COPY pyproject.toml poetry.lock README.md ./

# Install the required packages
RUN pip install poetry==2.1.2 --no-cache-dir && \
    poetry config virtualenvs.create false && \
    poetry lock && \
    poetry install --no-root

# Copy the rest of the application code into the container
COPY . .

# Final stage
FROM gcr.io/distroless/base-debian12:nonroot

WORKDIR /app

# Copy Python interpreter and libraries
COPY --from=build --chown=nonroot:nonroot /usr/local/bin/python3.12 /usr/local/bin/python3.12
COPY --from=build --chown=nonroot:nonroot /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=build --chown=nonroot:nonroot /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=build --chown=nonroot:nonroot /usr/local/lib/libpython3.12.so* /usr/local/lib/

# Copy system libraries
COPY --from=build --chown=nonroot:nonroot /usr/local/bin /usr/local/bin
COPY --from=build --chown=nonroot:nonroot /lib/* /lib/

# Copy application code
COPY --from=build --chown=nonroot:nonroot /app /app

# Expose the port Streamlit will run on
EXPOSE 8000
EXPOSE 8501 

# Switch to the non-root user
USER nonroot

# Command to run the Streamlit application
CMD ["streamlit", "run", "streamlit_app.py"]