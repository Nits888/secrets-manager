# Use the official Python image as the base image
FROM python:3.10

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt requirements.txt

# Install the required dependencies
RUN pip install -r requirements.txt

# Copy the entire project into the container's /app directory
COPY . /app
RUN find /app -type d -name "venv" -exec rm -rf {} \; || true

# Install Nginx
# RUN apt-get update && apt-get install -y nginx

# Remove default Nginx configuration
# RUN rm /etc/nginx/sites-enabled/default

# Copy SSL certificates
# ARG CERTIFICATE_PATH
# COPY ${CERTIFICATE_PATH}/certificate.pem /etc/nginx/ssl/
# COPY ${CERTIFICATE_PATH}/private_key.pem /etc/nginx/ssl/

# Copy your custom Nginx configuration
# COPY nginx.conf /etc/nginx/sites-available/myapp
# RUN ln -s /etc/nginx/sites-available/myapp /etc/nginx/sites-enabled

# Expose port 443 for HTTPS
EXPOSE 443

# Set an environment variable for the container name
ENV CONTAINER_NAME=my-secrets-manager

# Run the Flask app using Waitress
# CMD ["bash", "-c", "service nginx start && waitress-serve --listen=0.0.0.0:7443 main.cry_secrets_manager:app"]
CMD ["waitress-serve", "--listen=0.0.0.0:7443", "main.cry_secrets_manager:app"]