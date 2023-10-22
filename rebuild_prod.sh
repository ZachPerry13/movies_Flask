docker image prune --all && docker system prune -af
docker build -t my-flask-app .
docker run -it -p 443:443 my-flask-app