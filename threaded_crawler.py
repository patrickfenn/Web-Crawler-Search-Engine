import json
from bs4 import BeautifulSoup
import requests
import validators
from validators import ValidationFailure
from concurrent.futures import ThreadPoolExecutor, as_completed


class Crawler:        
    
    def __init__(self, seed, scan_depth_limit):
        self.main_seed = seed
        self.main_url_set = set()
        self.scan_depth_limit = scan_depth_limit

    def check_link(self, link):
        try:
            result = validators.url(link)
        except Exception as e:
            return False

        if isinstance(result, ValidationFailure):
            return False

        return True
    

    def get_seed(self, link):
        if self.check_link(link):
            r = requests.get(link)
            soup = BeautifulSoup(r.text, 'html.parser')
            return soup
        else:
            return None

    
    #gets all links on a page. grabs anythin with an <a href tag so some are garbage (like '#')
    def get_dirty_links(self, soup_obj):
        if soup_obj == None:
            return set()

        dirty_links = set()
        unparsed_links = soup_obj.findAll('a')
        if unparsed_links == None:
            return set()

        for link in unparsed_links:
            if link.has_attr('href'):
                new_dirty_link = link['href']
                if "https://www.bjpenn.com/mma-news/" in new_dirty_link:

                    dirty_links.add(new_dirty_link) 
        
        return dirty_links

                  
    def getCurrentLinkSet(self):
        return self.main_url_set.copy()

    def start(self, threads = 10):
        with ThreadPoolExecutor(threads) as executor:
            futures = []
            main_seed_soup = self.get_seed(self.main_seed)
            
            def async_recursive_crawl(soup, url_acc, scan_depth):
                # get only the unique links in the page
                unique_links = self.get_dirty_links(soup).difference(url_acc)

                if(len(unique_links) != 0):
                    # union the two unique sets
                    url_acc |= unique_links
                
                if(scan_depth >= self.scan_depth_limit): 
                    return url_acc

                for link in unique_links:
                    futures.append(executor.submit(async_recursive_crawl, self.get_seed(link), url_acc, scan_depth + 1))

                #After making threads crawl the unique links return the unique links found on this page
                return url_acc

            futures.append(executor.submit(async_recursive_crawl, main_seed_soup, set(), 0))

            for future in as_completed(futures):
                self.main_url_set |= future.result()

    def get_data_from_link(self, link):
        text = ""
        seed = self.get_seed(link)

        if seed == None:
            return ""
        
        p_tags = seed.findAll('p')
        try:
            for p_tag in p_tags:
                text += p_tag.getText()
        except(...):
            True

        return ({
            'title': seed.title.text,
            'url' : link,
            'text': ''.join(s for s in text if ord(s)>31 and ord(s)<126)
        })

    def generate_and_store_jsons(self, threads):       
        data_list = [] 

        executor = ThreadPoolExecutor(threads)
        data_futures = [executor.submit(self.get_data_from_link, url) for url in self.main_url_set]  

        for future in as_completed(data_futures):
            data_list.append(future.result())

        with open('Data.json', 'w') as jfile:
            jfile.write(json.dumps(data_list, indent=4, separators=(',\n', ': ')))
            

        
        



if __name__ == "__main__":
    seed = "https://www.bjpenn.com/mma-news/ufc/jairzinho-rozenstruik-warns-marcin-tybura-of-his-power-ahead-of-ufc-273-as-soon-as-i-start-touching-people-they-have-big-problems/"
    depth_limit = 2
    crawler_threads = 15
    json_threads = 15
    spider = Crawler(seed, depth_limit)
    
    print(f"Crawler started\n\tDepth limit: {depth_limit}\n\tThreads used: {crawler_threads}")
    spider.start(crawler_threads)
    print(f"Crawling completed.\n\tLinks collected: {len(spider.getCurrentLinkSet())}")
    print(f"Saving information to Data.json...\n\tThreads used: {json_threads}")
    spider.generate_and_store_jsons(json_threads)
    print(f"All data saved to Data.json")