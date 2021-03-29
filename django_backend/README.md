# Backend part

## Preliminary requirements
Before we run the backend server, the Redis service should have been already started. The port as default should be 6379.

## Run
Run the bash script "run_backend.sh" to start running the backend server.
```angular2html
bash ./run_backend.sh
```
        
If you want to change the runserver port, change this command in the script:
```
python3 manage.py runserver 0.0.0.0:8000
```
to 
```
python3 manage.py runserver 0.0.0.0:80
```
