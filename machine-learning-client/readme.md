to build the docker image, in this dir:

```bash
docker build -t ml-client .
```

to run the ml client server

```bash
docker run --rm -p 5000:5000 ml-client
```

to confirm the server is up, you will get a json response supposedly

```bash
curl http://localhost:5000/health
```

a sample request to send a picture

```bash
curl -F "image=@images/sad.jpg" http://localhost:5000/analyze
```
