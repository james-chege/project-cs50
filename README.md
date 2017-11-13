# project-cs50
# Configuration:
on a command prompt or a terminal create a python working environment, here is a quick way to do this(virtualenvwrapper.readthedocs.io/en/latest/) and navigate your way 
			   to the project's directory.
			   Run the following commands: [pip install -r requirements.txt] followed by [export FLASK_APP=app.py] followed by [export FLASK_DEBUG=1]
			   On the same terminal on the project's directory run following command [python] , a python shell will appear and on that shell type this command [from app import db]to import the database from the app and while still on that shell type the following command [db.create_all()] to create the models. 
			   Type [exit()] to exit the shell.
			   You can access the database on a terminal by typing the following command on the project's directory [sqlite3 database.db]
			   Finally type the following command [flask run] and visit [localhost:5000] in your browser.

This project is cloned from my a private repo to help a learner have an idea on how to do a flask project one module app.
Thanks to Zamyla and Irene naya for such a great support via walkthroughs and answering questions.
