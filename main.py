import selenium
from selenium import webdriver
import time
from selenium.webdriver.common.by import By
import os
import re
import requests
from selenium_stealth import stealth
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

class GetSource():
    source_file = 'demo.txt'
    finalFile = "result.txt"
    # The channel names in this list will continue to use URLs from the demo. These will take precedence over the latest source, allowing us to gather more URLs and compare their speeds.
    importantList = ['珠江', '开平综合', '开平生活', 'CCTV1', 'CCTV5', 'CCTV5+', 'CCTV13', '广东体育', '广东卫视', '大湾区卫视', '浙江卫视', '湖南卫视', '翡翠台']
    importantUrlsNum = 10

    def __init__(self):
        self.driver = self.setup_driver()
        self.main()

    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")
        options.add_argument('--headless')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("blink-settings=imagesEnabled=false")
        driver = webdriver.Chrome(options=options)
        stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        )
        return driver

    def getChannelItems(self):
        # Open the source file and read all lines.
        with open(self.source_file, 'r') as f:
            lines = f.readlines()

        # Create a dictionary to store the channels.
        channels = {}
        current_channel = ''
        pattern = r"^(.*?),(?!#genre#)(.*?)$"

        for line in lines:
            line = line.strip()
            if '#genre#' in line:
                # This is a new channel, create a new key in the dictionary.
                current_channel = line.split(',')[0]
                channels[current_channel] = {}
            else:
                # This is a url, add it to the list of urls for the current channel.
                match = re.search(pattern, line)
                if match:
                    if match.group(1) not in channels[current_channel]:
                        channels[current_channel][match.group(1)] = [match.group(2)]
                    else:
                        channels[current_channel][match.group(1)].append(match.group(2))
        return channels

    def getSpeed(self,url):
        start = time.time()
        try:
            r = requests.get(url,timeout=5)
            resStatus = r.status_code
        except:
            print('request timeout or error')
        end = time.time()
        return url, end - start

    def compareSpeed(self,pageUrls):
        response_times = []
        with ThreadPoolExecutor(max_workers=self.importantUrlsNum) as executor:
            future_to_url = {executor.submit(self.getSpeed, url): url for url in pageUrls}
            for future in concurrent.futures.as_completed(future_to_url):
                url, response_time = future.result()
                response_times.append((url, response_time))
        sorted_urls = sorted(response_times, key=lambda x: x[1])
        pageUrls_new = [url for url, _ in sorted_urls]
        return pageUrls_new
    
    def removeFile(self):
        if os.path.exists(self.finalFile):
            os.remove(self.finalFile)

    def outputTxt(self,cate,channelUrls):
        # Update the final file.
        with open(self.finalFile, 'a') as f:
            f.write(cate + ',#genre#\n')
            for name, urls in channelUrls.items():
                for url in urls:
                    f.write(name + ',' + url + '\n')
            f.write('\n')

    def visitPage(self,channelItems):
        self.driver.get("https://www.foodieguide.com/iptvsearch/")
        self.removeFile()
        for cate, channelObj in channelItems.items():
            channelUrls = {}
            for name in channelObj.keys():
                element=self.driver.find_element(By.ID, "search")
                element.clear()
                element.send_keys(name)
                self.driver.find_element(By.ID, "form1").find_element(By.NAME,"Submit").click()
                urls=[]
                isImportant = name in self.importantList
                useNum = self.importantUrlsNum if isImportant else 5
                allRangeElement=self.driver.find_elements(By.CLASS_NAME, "m3u8")
                if len(allRangeElement)<=0:
                    continue
                if len(allRangeElement)>useNum:
                    allRangeElement=allRangeElement[:useNum]
                for elem in allRangeElement:
                    urls.append(elem.text)
                # urls=self.compareSpeed(urls) if isImportant else urls
                allUrls=list(dict.fromkeys(channelObj[name] + urls if isImportant else urls))
                channelUrls[name]=allUrls
            self.outputTxt(cate,channelUrls)
            time.sleep(1)

    def main(self):
        self.visitPage(self.getChannelItems())

GetSource()
