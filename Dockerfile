# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY ./our-crm-ai/requirements.txt /app/

# Install any needed packages specified in requirements.txt
# Using CPU-only torch index to keep the image size smaller
RUN pip install --no-cache-dir -r requirements.txt \
    --extra-index-url https://download.pytorch.org/whl/cpu

# Copy the rest of the application's code into the container
COPY ./our-crm-ai /app/our-crm-ai

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=our-crm-ai/api.py
ENV ANTHROPIC_API_KEY="" # This should be set at runtime
ENV YOUGILE_API_KEY="" # This should be set at runtime

# Run the command to prepare the RAG index first
RUN python3 our-crm-ai/rag/rag_system.py prepare

# Run api.py when the container launches
CMD ["flask", "run", "--host=0.0.0.0"]
