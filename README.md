#genwiki

Personal wiki

##Importing legacy wiki

Use the import API:
```
import requests
requests.post('http://localhost:8080/wiki/import', files=dict(upload=('wiki.zip', open('wiki.zip', 'rb'))))
```
