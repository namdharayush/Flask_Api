import requests
from lxml import html
import json


url = 'https://www.linkedin.com/jobs/view/4137266502/'
api = 'http://127.0.0.1:5000/api/job_id?job_id=4137266502&job_id=4153148207&job_id=4136809662'



response = requests.get(api).json()
print(json.dumps(response))