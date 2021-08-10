# BestJobApp (Aiohttp)
_____________________________
## Description
This web application written on Aiohttp is an API which allows candidates to find a position with they find interesting, offered by an employer's representative.
The process of signing an offer divided to three stages:

1. Creating a job offer by employer
2. Getting information of a job offer
3. Signing a job offer by a candidate

Although only one candidate can sign a job offer, an employer can offer a job to multiple candidates. First one who signs gets the job.

## Preparation
Important!
Make sure that you have installed PostgreSQL database: http://www.postgresql.org/download/.

Install required modules:
```
  pip install -r requirements.txt
```
Create database fill it with test data:
```
  python3 init_db.py setup
```
If you want to delete created db and all associated data with this app, use the parameter `teardown` instead of `setup`.
```
  python3 init_db.py teardown
```

## Launch
Start app:
```
  python3 app/main.py
```
Swagger documentation can be found:
http://0.0.0.0:8080/docs




