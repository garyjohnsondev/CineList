CineList.io
------------------------
#### System Requirements / Tool Stack:
* **Python 3** - [Download](https://www.python.org/downloads/)
* **Django** - [Download](https://www.djangoproject.com/download/)
* **PostgreSQL** - [Download](https://www.postgresql.org/download/)

Other packages (these can also be installed using conda):
```
pip install psycopg2-binary       # if using postgreSQL
pip install django-crispy-forms
```

****

#### Step-By-Step Build Instructions
1. Clone our repository:
    ```
    git clone https://github.com/usu-cs-3450/Repo-2.3.git
    ```
2. Open the cloned directory in an IDE or in a CLI   ``cd /path/to/Repo-2.3/cinelist``.
3. Our system can be run locally using PostgreSQL or SQLite. To use SQLite, comment out the PostgreSQL config and uncomment the SQLite config under the `DATABASES` setting in `/cinelist/settings.py`.  

To run locally (the `dropdb` and `createdb` commands are for PostgreSQL users):
```
dropdb cinelist_dev                     
createdb cinelist_dev                    
python manage.py migrate
python manage.py loaddata genres.json users.json
python manage.py runserver
```
4. Go to http://localhost:8000/
5. To log in using a test user account, see below.

__If you have a bash-enabled CLI, you may instead run one the following scripts to automate the install process.__  

For a fresh install using PostgreSQL (also installs required python packages):
```
sh scripts/install.sh
```
To flush existing database and install fixtures using PostgreSQL or SQLite (can also be used to init a new SQLite database if none exists yet -- make sure to follow step 3 above):
```
sh scripts/update.sh
```

****
#### Testing
Unit tests are implemented using Django's automated testing and Python `unittest`. To run all unit tests, execute the following command:
```
python manage.py test
```


------------------------
## CS3450 Phase Deliverables can be found in the /deliverables directory.
##### Notes:
* Our README is always located in the outer project folder.
* Neither the Project Plan or Requirements Definition have changed from Phase 1.

##### Test Users
**Name:** Demo Superuser  
**username:** demo_superuser  
**password:** superuser    

**Name:** Richard Clark  
**username:** richard.clark65  
**password:** bootsy65  

**Name:** Marion Andrews  
**username:** marionws  
**password:** peacock41  

**Name:** Tina Marshall  
**username:** tina  
**password:** apples74  

**Name:** Brandon George  
**username:** brandongeorge  
**password:** golden134  
