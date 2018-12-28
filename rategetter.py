import time
import sys
import os
import re


USERNAME = "cac9159"
PASSWORD = "password"
URL      = "http://www.site.com"



proxies  = {
    'http' :'http://'+USERNAME+':'+PASSWORD+'@proxy.cna.com:8080/',
    'https':'http://'+USERNAME+':'+PASSWORD+'@proxy.cna.com:8080/',
    }

headers  = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.117 Safari/537.36'}

r = requests.get(URL, headers=headers, proxies=proxies)
rtext = r.content.decode('utf-8','ignore')

# Regular expression to extract rates: >(\$\d+)(?=</span></strong><br />)
matched = re.findall(r">(\$\d+)(?=</span></strong><br />)", rtext)

# matched is a list containing extracted rates