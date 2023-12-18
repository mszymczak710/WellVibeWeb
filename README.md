# WellVibeWeb

## Introduction

WellVibeWeb is a clinic management system developed as an engineering project in the field of Computer Science at the Faculty of Mathematics and Informatics, Nicolaus Copernicus University in Toruń. The aim of the project is to design and implement a web application for clinic management that addresses the needs of patients, doctors, and administrators. The application enables patients to access their visit history and prescriptions, doctors to manage appointments and prescriptions, and administrators to have control over the processes.

## Technology Stack

The WellVibeWeb application utilizes a robust technology stack including:

- **PostgreSQL 16**: A powerful, open-source object-relational database system. [More about PostgreSQL 16](https://www.postgresql.org/)
- **Django 5.0**: A high-level Python web framework that encourages rapid development and clean, pragmatic design. [More about Django 5.0](https://www.djangoproject.com/)
- **Angular 17**: A platform for building mobile and desktop web applications using TypeScript/JavaScript and other languages. [More about Angular 17](https://angular.io/)

## Environment Configuration

To configure the environment for WellVibeWeb, you need to copy the contents of the `.env.sample` file into a new file named `.env` and adjust the environment variable values according to your needs. The `.env` file will contain all the necessary configuration information required by the application.

### Step by Step

1. **Navigate to the Docker Directory**:
   Before copying the configuration file, make sure to navigate to the `docker` directory within the project:

   ```bash
   cd docker

2. **Copy the Configuration File**:
   Copy the `.env.sample` file to a new file named `.env` in the main project directory.

   ```bash
   cp .env.sample .env
   ```

3. **Edit the `.env` File**:
   Open the `.env` file in a text editor and fill in the following environment variables:

   - `DB_NAME`: The name of your database.
   - `DB_USER`: The username for the database.
   - `DB_PASSWORD`: The password for the database.
   - `DB_HOST`: The database host (use 'db' for Docker).
   - `DB_PORT`: The database port (default is 5432 for PostgreSQL).
   - `DJANGO_SECRET_KEY`: Your Django secret key.
   - `DJANGO_SUPERUSER_FIRST_NAME`: The first name of the Django superuser.
   - `DJANGO_SUPERUSER_LAST_NAME`: The last name of the Django superuser.
   - `DJANGO_SUPERUSER_EMAIL`: The email of the Django superuser.
   - `DJANGO_SUPERUSER_PASSWORD`: The password for the Django superuser.
   - `EMAIL_HOST`: The email server host (e.g., smtp.gmail.com).
   - `EMAIL_PORT`: The email server port (default is 587).
   - `EMAIL_USE_TLS`: Whether to use TLS (set to True).
   - `EMAIL_HOST_USER`: The email host user.
   - `EMAIL_HOST_PASSWORD`: The email host password.
   - `DEFAULT_FROM_EMAIL`: The default from email address.
   - `EMAIL_FILE_PATH`: The path for storing emails (for testing purposes).
   - `RECAPTCHA_SECRET_KEY`: Your reCAPTCHA secret key.
   - `RECAPTCHA_VERIFY_URL`: The URL for reCAPTCHA verification.
   - `TEST_DB_NAME`: The name of the test database.

4. **Save the `.env` File**:
   After filling in and saving the changes in the `.env` file, the application will be ready to run.

## Building and Running the Application

To build and run WellVibeWeb using `docker-compose`, follow these steps:

1. **Build the Containers**:
   Before running the application for the first time, you need to build the containers. In the main project directory, run the following command:

   ```bash
   docker-compose build
   ```

2. **Run Docker-Compose**:
   To start the application, use the command:

   ```bash
   docker-compose up
   ```

   This command will start the containers defined in the `docker-compose.yml` configuration.

3. **Access the Application**:
   Once the containers are running, WellVibeWeb will be accessible at
   [http://localhost:8000/api/](http://localhost:8000/api/).

4. **Access the Django Admin Panel**:
   To use the Django administrative panel, navigate to [http://localhost:8000/admin/](http://localhost:8000/admin/) on your web browser. Here, you can log in using the credentials set for the Django superuser. The login details are as follows:
      - **Email**: Use the email address specified in the `DJANGO_SUPERUSER_EMAIL` environment variable.
      - **Password**: Use the password set in the `DJANGO_SUPERUSER_PASSWORD` environment variable.

   This panel provides administrative control over the application, allowing you to manage various aspects of the system, such as user accounts, appointments, and other data relevant to clinic management.

## Testing

To perform tests, use the command:

```bash
docker-compose exec -it api pytest <full_path_to_test>
```

Replace `<full_path_to_test>` with the actual path to the test file you wish to run.

## Help

If you encounter any issues while setting up or running WellVibeWeb, please contact <mszymczak710@o2.pl>.
