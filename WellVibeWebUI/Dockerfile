FROM node:18

# Set the working directory in the container
WORKDIR /code

# Copy the `package.json` and `package-lock.json` files (if available)
COPY . .

# Install Angular
RUN npm install -g @angular/cli

# Install project dependencies
RUN npm install

# Expose the port Angular serves on
EXPOSE 4200

# Run the application using `ng serve`
CMD ["ng", "serve", "--host", "0.0.0.0", "--poll=2000"]