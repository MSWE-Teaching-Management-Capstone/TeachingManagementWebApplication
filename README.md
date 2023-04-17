# Teaching Management Web App 

## Tech Stack
- Back-end framework: Flask
- Database: SQLite3

## Project Setup

### Prerequisite
- Python version: python 3.9 or newer

### Instruction
1. Use `Git` to clone the repo to local machine.
```shell
git clone https://github.com/MSWE-Teaching-Management-Capstone/TeachingManagementWebApplication.git

```

2. Create a `.flaskenv` file and `.env` file to put flask env variables under the root directory.

2.1 **In the `.flaskenv` file**
```shell
# Linus/MacOS
export FLASK_APP='management_app'
export FLASK_DEBUG='true'

# Windows
set FLASK_APP='management_app'
set FLASK_DEBUG='true'
```
2.2 **In the `.env` file**
```shell
# Linus/MacOS
export GOOGLE_CLIENT_ID='559245110133-8bog3pa5k75ih9q1fkkauiv8latmbgjf.apps.googleusercontent.com'
export DOMAIN="uci.edu"

# Windows
set GOOGLE_CLIENT_ID='559245110133-8bog3pa5k75ih9q1fkkauiv8latmbgjf.apps.googleusercontent.com'
set DOMAIN="uci.edu"
```

> Note that the `.flaskenv` and `.env` file will store at your local instead of repository. We can discuss if we would like to publish this file when we deploy.

3. Create a virtual environment and activate it.

Let's create our virtual environment is in a directory called 'venv'.

```shell 
cd TeachingManagementWebApplication

# For macOS/Linux
python3 -m venv venv

# For Windows
py -3 -m venv venv
```

> After the above, verify the virtual environment is activated and currently used by typing `which python3` in your terminal.
It should look like this `...../TeachingManagementWebApplication/venv/bin/python3`

4. Activate the virtual machine
```shell
# For macOS/Linux
. venv/bin/activate

# For Windows
venv\Scripts\activate
```

> If you don't need the virtual machine anymore, run the following command to deactivate venv
> ```
> deactivate
> ```

5. Install the third-party packages if needed
```Shell
pip install -r "requirements.txt"
```

6. If you set up database for the first time, initialize the sqlite database
There will now be a management_app.sqlite file in the instance folder in your project.

```shell
flask init-db
```

7. Run the Web application locally

```shell
flask run
```
The web browser will run at `http://127.0.0.1:5000/` on the browser.

## Run Testing

To run testing in virutal environment, use the command below after activating your venv:
```shell
python -m pytest
```

`Pytest` will collect the files name starting `test_` under tests folder.

To run test suites in only one test file, use the command below then run that file under tests folder:
```shell
python -m pytest tests/test_file_name
```

We use py-cov plugin to run the unit test coverage report on the command line. For generating different format of report, please refer to [py-cov document](https://pytest-cov.readthedocs.io/en/latest/).
```shell
python -m pytest --cov=management_app
```

If you want to check terminal report with missing line numbers:
```shell
python -m pytest --cov-report term-missing --cov=management_app
```

## Project Deploy
It is not ready but some instructions of how to access the Virtual Machine hosted in UCI ICS server. Please refer to our Wiki page to learn more details.

## Reference
- https://plainenglish.io/blog/flask-crud-application-using-mvc-architecture
- https://flask.palletsprojects.com/en/2.2.x/tutorial/layout/

## Team Members:
- [Can Wang](mailto:canw7@uci.edu)
- [Ying-ru Fang](mailto:yingruf1@uci.edu)
- [Justin Lock](mailto:jjlock@uci.edu)
- [Yu-che Su](mailto:yuches@uci.edu)
