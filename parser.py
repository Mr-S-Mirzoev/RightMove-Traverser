import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
from copy import deepcopy
import json

class Property:
    def __init__(self, link: str, text: str, title: str):
        self.text = text
        self.link = link
        self.title = title
        self.key_features = list()
        self.tenureType = str()
        self.get_info()
        
    def get_info(self):
        kf = self.text.find('<h3>Key features</h3>')
        if kf != -1:
            li_start = self.text.find('<li>', kf)
            li_end = self.text.find('</ul>', li_start)
            self.key_features = self.get_key_features(self.text[li_start:li_end].strip())
        tt = self.text.find('<span id="tenureType">')
        if tt != -1:
            tt_start = tt + len('<span id="tenureType">')
            tt_end = self.text.find('</span>', tt)
            self.tenureType = self.text[tt_start:tt_end]
        ds = self.text.find('<p itemprop="description">')
        if ds != -1:
            ds_start = ds + len('<p itemprop="description">')
            ds_end = self.text.find('</p>', ds_start)
            description = self.text[ds_start:ds_end].replace('<br/>',' ').replace('\r',' ').replace('\n', ' ').replace('<strong>', ' ').replace('</strong>', ' ')
            description = description.replace('&amp;', '&').replace('<b>','').replace('</b>', ':').replace('<p>', '')
            self.description = ' '.join(description.strip().split())
            if not self.tenureType:
                if self.description.lower().find('free hold') != -1:
                    self.tenureType = 'Freehold'
                elif self.description.lower().find('freehold') != -1:
                    self.tenureType = 'Freehold'
                elif self.description.lower().find('lease') != -1:
                    self.tenureType = 'Freehold'

    def dump_as_dict(self) -> dict:
        dct = dict()
        dct['Tenure type'] = self.tenureType
        dct['Link'] = self.link
        dct['Title'] = self.title
        dct['Key features'] = self.key_features
        dct['Description'] = self.description
        return dct        

    def get_key_features(self, txt_kf) -> list:
        lst = txt_kf.split('\n')
        ret_lst = list()
        for line in lst:
            li_start = line.find('<li>') + 4
            li_end = line.find('</li>', li_start)
            value = line[li_start:li_end].strip()
            if value:
                ret_lst.append(value)
        return ret_lst


command = input().strip()
if command == 'c':
    command = 'continue'
elif command == 'r':
    command = 'reload'
if command.lower() == 'reload':
    links = list()
    for page in range(42):
        url = 'https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier=POSTCODE%5E619277&minBedrooms=2&maxPrice=350000&radius=30.0&sortType=1&index={}&propertyTypes=&includeSSTC=false&mustHave=&dontShow=&furnishTypes=&keywords='.format(24 * page)
        r = requests.get(url)
        start = 0
        while start != -1:
            last = 0
            start = r.text.find('propertyCard-details', last)
            href = str()
            href_start = r.text.find('href="', start) + len('href="')
            href_end = r.text.find('"', href_start)
            if href_start != -1 and href_end != -1:
                href = r.text[href_start:href_start]
                last = href_end
            else:
                last = start + 1
                
            if href:
                hreflink = 'https://www.rightmove.co.uk' + href
                links.append(hreflink + '\n')
        print(len(links))

    with open('links.txt', 'w') as link_file:
        link_file.writelines(links)
elif command.lower() == 'continue':
    m_date = str(datetime.fromtimestamp(os.path.getmtime(os.path.join('.', 'links.txt'))))
    modification_date = m_date[:m_date.find('.')]
    print('OK, walking through previous list, updated on {}'.format(modification_date))
    with open('links.txt', 'r') as link_file:
        links = [s.strip() for s in link_file.readlines()]
else:
    print('Command not found. Commands on this level: continue/reload')

for link in links:
    r = requests.get(link)
    soup = BeautifulSoup(r.text, "html.parser")
    boats = list()
    freehold = list()
    sharedownership = list()
    aged = list()
    lease = list()
    go_further = False
    b = soup.find('title')
    for val in b:
        strval = str(val).strip()
        if strval:
            title = strval[strval.find('>') + 1:strval.rfind('<')]
            if title.find('boat') != -1:
                boats.append(link)
                go_further = True
                break
    if go_further:
        continue
    else:
        b = soup.find('div', 'tabbed-content-tab-content description')
        if b:
            #print(b, end='\n\nOTHER\n')
            pr = Property(link, str(b), title).dump_as_dict()
            js = json.dumps(pr, indent=4, ensure_ascii=False).encode('utf8')
            print(js.decode())
    