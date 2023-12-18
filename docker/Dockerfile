FROM python:3.10.12

# Set environment variables
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /code

# Install netcat
RUN apt-get update && apt-get install -y netcat-openbsd

# Copy the WellVibeWebAPI project folder
COPY ./WellVibeWebAPI /code/WellVibeWebAPI/

# Install dependencies
RUN pip install -r WellVibeWebAPI/requirements.txt

# Copy the entrypoint script and make it executable
COPY ./docker/entrypoint.sh /code/
RUN chmod +x /code/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/code/entrypoint.sh"]
