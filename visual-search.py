from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import os
import re
import settings

with open(settings.links, 'r') as f:
    links = f.read().splitlines()

if settings.proxy:
    proxy = settings.proxy.split(':')
    profile = webdriver.FirefoxProfile() 
    profile.set_preference("network.proxy.type", 1)
    profile.set_preference("network.proxy.http", proxy[0])
    profile.set_preference("network.proxy.http_port", int(proxy[1]))
    profile.set_preference("network.proxy.ssl", proxy[0])
    profile.set_preference("network.proxy.ssl_port", int(proxy[1]))
    profile.update_preferences() 
    driver = webdriver.Firefox(firefox_profile=profile)
else:
    driver = webdriver.Firefox()
driver.get('https://www.pinterest.com')

# login:
username = driver.find_element_by_xpath('//input[@name="id"]')
username.click()
username.clear()
username.send_keys(settings.username)

password = driver.find_element_by_xpath('//input[@name="password"]')
password.click()
password.clear()
password.send_keys(settings.password)

button = driver.find_element_by_css_selector('button.SignupButton')
button.click()

time.sleep(5);

for link in links:
    if not link:
        continue
        
    # visit page:
    driver.get(link + 'visual-search')
    
    # extract pin id
    id = re.search(r'[0-9]+', link).group(0)

    # make directory for link
    if not os.path.exists(id):
        os.mkdir(id)

    with open(id + '/source.txt', 'wb') as f:
        # retrive source image
        while True:
            try:
                src = driver.find_element_by_css_selector('div.FlashlightEnabledImage').find_element_by_xpath('div/img');
                break
            except:
                pass
        src = src.get_attribute('src')
        print 'source:', src
        f.write(src)
        f.write('\n')

    with open(id + '/tags.txt', 'wb') as f:
        # retrive tag:
        while True:
            try:
                tags = driver.find_elements_by_class_name('flashlightAnnotationListItem')
                tags = map(lambda x: x.text, tags)
                if tags:
                    break
            except:
                pass
        tags = ','.join(tags)
        print 'tags:' , tags
        f.write(tags)
        f.write('\n')

    with open(id + '/search-results.txt', 'wb') as f:
        # retrive seach results:
        count = 0
        retry = 0
        while retry < 3 and count < settings.limit:
            driver.execute_script('var c = document.getElementsByClassName("flashlightResultsContainer")[0]; c.scrollTop = c.scrollHeight;')
            time.sleep(3)

            while count < settings.limit:
                try:
                    ics = driver.find_elements_by_css_selector('a.pinImageWrapper')
                    if len(ics) > count:
                        offset = count
                        for ic in ics[offset:]:
                            count += 1
                            if count > settings.limit:
                                break
                            img = ic.find_element_by_xpath('div/div/img');
                            src = img.get_attribute('src')
                            print "%5d: %s" % (count, src);
                            f.write(src)
                            f.write('\n')
                        retry = 0
                    else:
                        retry += 1
                        break
                except:
                    pass
driver.quit()
