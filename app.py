from flask import Flask, jsonify, request
import requests
from lxml import html
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=30)
import time
from bs4 import BeautifulSoup
import re
from flask_cors import CORS

app = Flask(__name__)

CORS(app)




def clean_text(text):
    text = re.sub(r"\n\s*\n", "\n\n", text)
    text = re.sub(r"(\w+)\n(\w+)", r"\1 \2", text)
    return text.strip()

def parse_job_details(response):
    try:
        sc = html.fromstring(response)
    except:
        sc = None
    
    if sc:
        
        try:
            job_post_link = ''.join(sc.xpath('//meta[@property="og:url"]/@content'))
        except:
            job_post_link = ''

        try:
            job_title = ''.join(sc.xpath('//h1/text()'))
        except:
            job_title = ''

        try:
            company_name = ''.join(sc.xpath("(//a[contains(@href,'company')])[1]/@title"))
        except:
            company_name = ''

        try:
            company_profile = ''.join(sc.xpath("(//a[contains(@href,'company')])[1]/@href")).split('?')[0]
        except:
            company_profile = ''

        try:
            location = ''.join(sc.xpath("(//a[contains(@href,'company')])[1]/following-sibling::span/text()"))
        except:
            location = ''

        try:
            job_posted_time = ''.join(sc.xpath("//span[contains(@class,'posted-time-ago')]/text()")).replace('\n','').replace('\t','').strip()
        except:
            job_posted_time = ''

        try:
            total_applicants = ''.join(sc.xpath("//figcaption/text()")).strip()
        except:
            total_applicants = ''

        try:
            job_apply_link = ''.join(set(sc.xpath('//div[@id="teriary-cta-container"]//a/@href')))
        except:
            job_apply_link = 'Easy Apply'
        
        if not job_apply_link:
            job_apply_link = 'Easy Apply'

        try:
            job_poster_profile = ''.join(sc.xpath("//div[@class='message-the-recruiter']//a[not(contains(@class,'message-the-recruiter'))]/@href"))
        except:
            job_poster_profile = ''

        try:
            job_poster_name = ''.join(sc.xpath("//div[@class='message-the-recruiter']//h3/text()")).strip()
        except:
            job_poster_name = ''

        try:
            job_poster_current_position = ''.join(sc.xpath("//div[@class='message-the-recruiter']//h4/text()")).strip()
        except:
            job_poster_current_position = ''

        job_criteria = {}
        try:
            all_job_desc_criteria = sc.xpath('//ul[@class="description__job-criteria-list"]/li')
        except:
            all_job_desc_criteria = []

        if all_job_desc_criteria:
            for each_criteria in all_job_desc_criteria:

                try:
                    criteria_key = ''.join(each_criteria.xpath('./h3/text()')).strip()
                except:
                    criteria_key = ''

                try:
                    criteria_value = ''.join(each_criteria.xpath('./span/text()')).strip()
                except:
                    criteria_value = ''

                if criteria_key:
                    job_criteria[criteria_key] = criteria_value
        
        job_post_description = ''

        try:

            soup = BeautifulSoup(response,'html.parser')
            selectors = [
                "article.jobs-description__container",
                "div.description__text.description__text--rich"
            ]

            job_desc_html = None

            for selector in selectors:
                job_desc_section = soup.select_one(selector)
                if job_desc_section:
                    job_desc_html = job_desc_section
                    break

            if not job_desc_html:
                print("Job description not found.")

            # Clean up the extracted text
            for tag in job_desc_html.find_all(["span", "strong", "b"]):
                tag.unwrap()

            for tag in job_desc_html.find_all("br"):
                tag.replace_with("\n")

            job_description = job_desc_html.get_text(separator="\n").strip()
            formatted_description = clean_text(job_description).replace('\n',' ').replace('Show more','').replace('Show less','').strip()  # Fix formatting issues

            job_post_description = formatted_description
        except:
            job_post_description = ''
        
        data = {
            'job_post_link' : job_post_link,
            'job_title' : job_title,
            'job_post_description' : job_post_description,
            'company_name' : company_name,
            'company_profile' : company_profile,
            'location' : location,
            'job_posted_time' : job_posted_time,
            'total_applicants' : total_applicants,
            'job_apply_link' : job_apply_link,
            'job_poster_profile' : job_poster_profile,
            'job_poster_name' : job_poster_name,
            'job_poster_current_position' : job_poster_current_position,
            'job_criteria' : job_criteria
        }

        return data
        
    return None
    
    




def fetch_job_details(job_id):
    
    url = f"https://www.linkedin.com/jobs/view/{job_id}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    }
    response = None
    for _ in range(5):
        try:
            response = requests.get(url, headers=headers)
        except:
            try:
                response = requests.get(url, headers=headers)
            except:
                try:
                    response = requests.get(url, headers=headers)
                except:
                    try:
                        response = requests.get(url, headers=headers)
                    except:
                        response = None
                        
        if response.status_code == 200:
            break
        if response.status_code == 404:
            return {"job_id": job_id, "status": response.status_code, "message": "This job post is not available"}
        time.sleep(10)
    if response and response.status_code == 200:
        data = parse_job_details(response=response.text)
        return {"job_id": job_id, "status": response.status_code, "content": data}
    return {"job_id": job_id, "status": 403, "message": "Something went wrong!"}


@app.route('/api/v1')
def get_details():
    job_ids = request.args.getlist("job_id")
    print(job_ids)
    if not job_ids:
        return jsonify({"error": "Missing job_id parameter"}), 400
    
    results = list(executor.map(fetch_job_details, job_ids))

    return jsonify(results)
    
if __name__ == '__main__':
    app.run(debug=True)