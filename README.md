# Flask/Python database backed categories project for Udacity Full Stack Developer Nanodegree

This code is designed to run using the Flask framework using Python 2.7.

## Author
Simon Otter

## Details of where this application is being hosted
* IP address and SSH port: 35.161.55.89:2200
* URL to your hosted web application [http://ec2-35-161-55-89.us-west-2.compute.amazonaws.com/](http://ec2-35-161-55-89.us-west-2.compute.amazonaws.com/)

## Features
1. Google authentication
2. Persistent data store of Categories and Items
3. Responsive design

## Installation for running in the Udacity Vagrant Environment
1. Copy the contents of this folder and it's subfolders to your machine.
2. Create the database by running database_setup.py
3. Start the web server application by running application.py


## Installation in Linux with PostgreSQL db
### Set-up the Database
1. Install PostgreSQL: ```sudo apt-get -y install postgresql postgresql-contrib```.
2. Configure PostgreSQL user: ```sudo su && su - postgres```.
3. Access the PostgreSQL prompt: ```psql```.
4. Change the password for postgres role by typing:
```
\password postgres
ENTER YOUR PASSWORD
```
5. Enter ```\q``` to leave the psql command line.

### Set-up the Web Server
1. After configured the security basics a Linux machine, install Apache HTTP server: ```sudo apt-get install apache2```
2. Install the mod_wsgi Apache module: ```sudo apt-get install libapache2-mod-wsgi``` and enable it with: ```sudo a2enmod wsgi```
3. Create the necessary Flask application directory structure: ```mkdir /var/www/categories```
4. Clone this github repository: ```git clone https://github.com/simonotter/Categories.git```
5. In the file ```database_setup.py```, change the database connection string to connect to the PostgreSQL by changing ```engine = create_engine('sqlite:///catalog.db')``` to ```engine = create_engine('postgresql://catalog:DB-PASSWORD@localhost/catalog')```, where DB-PASSWORD is your unique password.
6. Rename the ```application.py``` file to ```__init__.py```, because this is what Flask expects.
7. In the file ```__init__.py```, change the database connection string to connect to the PostgreSQL by changing ```engine = create_engine('sqlite:///catalog.db')``` to ```engine = create_engine('postgresql://catalog:DB-PASSWORD@localhost/catalog')```, where DB-PASSWORD is the password you established in step 5 above.
8. Create a project in [Google Cloud](https://console.cloud.google.com/apis/credentials) and create a OAuth2 client ID using the linux web server's public URL for the Authorised JavaScript origin.
9. Download the JSON file from Google Cloud and replace this into the file ```google_client_secret.json```.
10. Edit the client_id string in the file ```templates/signin.html``` to be the new Client ID.  
11. Install Flask and Virtual Environment: ```sudo apt-get install python-pip && sudo pip install virtualenv```.
12. Create the virtual Environment: ```sudo virtualenv venv```
13. Activate the virtual Environment: ```source venv/bin/activate```
14. Install Flask ```sudo pip install Flask```
15. Test if the installation has been successful and the app is running: ```sudo python __init__.py```, which should yield “Running on http://localhost:5000/” or "Running on http://127.0.0.1:5000/"
16. Deactivate the test with: ```deactivate```
17. Create a WSGI configuration file /var/www/Categories/categoriesapp.wsgi: ```touch /var/www/Categories/categoriesapp.wsgi```
18. Add the contents of the categoriesapp.wsgi file, should be as described in the section below.
19. Create the Apache virtual host: ```sudo nano /etc/apache2/sites-available/categoriesapp.conf``` which should contain the contents in the section below, but replacing the ServerName and ServerAlias for the IP and DNS of your linux website.
20. Enable the VirtualHost with: ```sudo a2ensite categoriesapp```
21. Restart Apache: ```sudo service apache2 restart```
22. Visit your website to check the categories app is being served.

#### The categoreisapp.wsgi file
```python
#!/usr/bin/python
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/categories/")

from categories import app as application
application.secret_key = 'Add your secret key'
```

#### The categoriesapp.conf file
```xml
<VirtualHost *:80>
                ServerName 35.161.55.89
                ServerAdmin admin@mywebsite.com
                ServerAlias ec2-35-161-55-89.us-west-2.compute.amazonaws.com
                WSGIScriptAlias / /var/www/categories/categoriesapp.wsgi
                <Directory /var/www/categories/categories/>
                        Order allow,deny
                        Allow from all
                </Directory>
                Alias /static /var/www/categories/categories/static
                <Directory /var/www/categories/categories/static/>
                        Order allow,deny
                        Allow from all
                </Directory>
                ErrorLog ${APACHE_LOG_DIR}/error.log
                LogLevel warn
                CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
```

## References and Acknowledgements
1. [How To Deploy a Flask Application on an Ubuntu VPS](https://www.digitalocean.com/community/tutorials/how-to-deploy-a-flask-application-on-an-ubuntu-vps)
2. [How to Install PostgreSQL and phpPgAdmin on Ubuntu](https://www.howtoforge.com/tutorial/ubuntu-postgresql-installation/)
3. Udacity Slack channel for linux_server_config project, particular thanks go to TrishW, Rahul Ranjan and myudacity99 for their help and advice.
