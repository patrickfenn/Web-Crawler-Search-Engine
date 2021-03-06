import json
from bs4 import BeautifulSoup
import requests
import validators
from validators import ValidationFailure
from tail_call_optimized import *


#How the JSON will be represented.
class entry:
    link = ""
    html_text = ""

    def __init__(self,l,h) :
        self.link = l 
        self.html_text  = h

    def __str__(self):
        return self.link + self.html_text

def bjpenn_crawler():

    def check_link(link):
        try:
            result = validators.url(link)
        except Exception as e:
            print(e)
            return False

        if isinstance(result, ValidationFailure):
             return False

        return True
    

    def get_seed(link):
   
        if check_link(link):
            r = requests.get(link)
            soup = BeautifulSoup(r.text, 'html.parser')
            return soup
        else:
            return None

    
    #gets all links on a page. grabs anythin with an <a href tag so some are garbage (like '#')

    def get_dirty_links(soup_obj):
        if not soup_obj:
            return []

        dirty_links = []
        unparsed_links = soup_obj.findAll('a')
        if not unparsed_links:
            return []

        for link in unparsed_links:
            if link.has_attr('href'):
                new_dirty_link = link['href']
                if "https://www.bjpenn.com/mma-news/" in new_dirty_link:

                    dirty_links.append(new_dirty_link)
        
        
        return dirty_links

   
    #recurse until terminate conditions are true, implemented with tail recursion (may need to modify server to expand stack limitation in python)
    @tail_call_optimized
    def recurse_get_dirty_links(soup_obj,link_dict):
        def terminate_check():
            return (len(link_dict) > 1)

        dirty_links = get_dirty_links(soup_obj)
        if dirty_links != []:
            for link in dirty_links:
                if link not in link_dict:
                    link_dict[link] = link

        for link in dirty_links:
            if terminate_check():
                
                return list(link_dict.values())

            recurse_get_dirty_links(get_seed(link),link_dict)


    #remove duplicates and possibly pre process further later on if needed
    def filter_links(dirty_link_list):

         if dirty_link_list == None:
             return []
        

         return dirty_link_list

    #Parses the text on the page by searching between <p> tags. Returns one single string with all the text.
    def get_text_from_link(link):
        text = ""
        seed = get_seed(link)
    
        if not seed:
            return ""
        
        p_tags = seed.findAll('p')
        try:
            for p_tag in p_tags:
                text += p_tag.getText()
        except(...):
            True

        return (''.join(s for s in text if ord(s)>31 and ord(s)<126))
  
    def get_web_page(link):
        try:
            req = requests.get(link)
        except requests.exceptions.InvalidSchema as i:
            print(i)
            return ""

        return req.text

    #creates the objects that the I will then convert to JSON objects
    def get_entries(clean_link_list):
        entries = []
        for clean_link in clean_link_list:
            new_entry = entry(clean_link, get_web_page(clean_link))
            entries.append(new_entry)

        return entries


    #converts entries to jsons
    def get_jsons(entries):
        json_list = []
      

        for entry in entries:
            json_list.append(json.dumps(entry.__dict__))

        return json_list

    #filters out pages that have no text on them
    def filter_jsons(dirty_jsons):
        """
        #Not needed for html file.
        for i in range( len(dirty_jsons) ):
            loaded_json = json.loads(dirty_jsons[i])
            if loaded_json['text'] == '':
                del dirty_jsons[i]"""
        

        return dirty_jsons
        
    def store_jsons(filtered_jsons):
        if len(filtered_jsons) == 0:
            print('filetered_jsons IS EMPTY')
            return

        big_json = "[\n"

        for i in range(len(filtered_jsons)):

            big_json += '\t' + filtered_jsons[i]

            if i < len(filtered_jsons) - 1:
                big_json += ','

        big_json += "\n]"

        with open('Data.json', 'w') as jfile:
            jfile.write(big_json)


  
    seed_url = "https://www.bjpenn.com/mma-news/"
    seed = get_seed(seed_url)
    link_list = recurse_get_dirty_links(seed,{})
    filtered_link_list = filter_links(link_list)
    print(len(filtered_link_list))
    entries = get_entries(filtered_link_list)
    json_objects = get_jsons(entries)
    filtered_jsons = filter_jsons(json_objects)
    print(entries[0])
       

def main():
   bjpenn_crawler()


if __name__ == "__main__":
    main()