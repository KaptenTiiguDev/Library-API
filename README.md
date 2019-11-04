# Library-API

A simple API for handling patrons, books and book issuing.

## Installation

To run the application, follow the steps below:

* Install Python, Pipenv and Postgres on your machine
* Clone the repository ```git clone git@github.com:MarjanaVoronina/Library-API.git```
* Change working directory to ```cd Library-API```
* Activate the virtual environment with ```pipenv shell command```
* Install all required dependencies with ```pipenv install```
* Export the required environment variables
```bash
export FLASK_ENV=development
export DATABASE_URL=postgres://name:password@host:port/library_api_db
export JWT_SECRET_KEY=taKbWfacbbNabz7og9Oa
```
* Run migrations ```./manage.py db init; ./manage.py db migrate; ./manage.py db upgrade```
* Start the app with ```./run.py```
