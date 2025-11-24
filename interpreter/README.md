# Interpreter

### Init the project

Create the virtual environment
~~~ bash
python3 -m venv .venv
~~~

Activate the venv
~~~ bash
source .venv/bin/activate
~~~


Install requirements
~~~ bash
pip install -r requirements.txt
~~~


## Architecture of the project

~~~ bash
src
├── main.py     # Entry points
├── controller/ # A folder to manage routes
├── service/    # logic and interactions
└── model/      # basic models
~~~
