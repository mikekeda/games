Games
======================

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/705d72004f7f46daa23202e59cc4718a)](https://app.codacy.com/manual/mikekeda/games?utm_source=github.com&utm_medium=referral&utm_content=mikekeda/games&utm_campaign=Badge_Grade_Dashboard)

This is site where you can play board games.
Link to the site - [https://games.mkeda.me](https://games.mkeda.me)

Available Games
------------
-   **Tic-tac-toe** - Game for two players, X and O, who take turns marking the spaces in a 3×3 grid.

Installation
------------
    # Install Redis
    sudo apt install redis-server
    # Install postgresql
    sudo add-apt-repository "deb http://apt.postgresql.org/pub/repos/apt/ xenial-pgdg main"
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
    sudo apt-get update
    sudo apt-get install postgresql-10
    # Configure database
    sudo su - postgres
    psql
    CREATE USER games_admin WITH PASSWORD 'home_pass';
    CREATE DATABASE games;
    GRANT ALL PRIVILEGES ON DATABASE games to games_admin;
    # Install packages
    pip install -r requirements.txt
    # Apply migrations
    python manage.py migrate
    # Create an admin user
    python manage.py createsuperuser

Running
-------
    # Locally
    python manage.py runserver

Upgrade python packages
-------
    # Remove versions from requirements.txt
    # Upgrade python packages
    pip install --upgrade --force-reinstall -r requirements.txt
    # Update requirements.txt
    pip freeze > requirements.txt

Useful manage.py commands
-------
    # Run tests
    python manage.py test
    # Run tests and check code style and coverage
    python manage.py jenkins --enable-coverage --pep8-exclude migrations --pylint-rcfile .pylintrc
