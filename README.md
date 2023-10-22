Work in progress, run main.py to spin up flask server (frontend and backend/api)

sudo docker build -t myflaskapp .
sudo docker-compose up
sudo docker-compose down


docker image prune --all && docker system prune -af


#TO REBUILD DEV ENV
docker-compose down
docker build -t myflaskapp .
docker-compose up


PROD
docker build -t my-flask-app .
docker run -it -p 443:443 my-flask-app