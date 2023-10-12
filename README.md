Work in progress, run main.py to spin up flask server (frontend and backend/api)

docker build -t myflaskapp .
docker-compose up
docker-compose down


docker image prune --all
docker system prune -af
