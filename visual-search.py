from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import os
import re
import settings

def get_all_links():
    with open(settings.links, 'r') as f:
        links = f.read().splitlines()
    return links

def create_driver():
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
        profile = webdriver.FirefoxProfile()
        profile.set_preference("network.proxy.type", 5)
        profile.update_preferences()
        driver = webdriver.Firefox(firefox_profile=profile)

    if settings.pageLoadtimeout:
        driver.set_page_load_timeout(settings.pageLoadtimeout)
    if settings.elementLoadTimeout:
        driver.implicitly_wait(settings.elementLoadTimeout)

    return driver

# login:
def login(driver):
    try:
        if not settings.username or not settings.password:
            print 'username or password not configured, quit'
            return False

        driver.get('https://www.pinterest.com/')

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

        return True
    except:
        return False

def getSource(driver):
    # retrive source image
    try:
        src = driver.find_element_by_css_selector('div.FlashlightEnabledImage div img');
        src = src.get_attribute('src')
    except:
        src = None
    return src

def saveSource(pid, src):
    with open(pid + '/source.txt', 'wb') as f:
        print '\tsource:', src
        f.write(src)
        f.write('\n')

def getTags(driver):
    # retrive tag:
    try:
        tags = driver.find_elements_by_class_name('flashlightAnnotationListItem')
        tags = map(lambda x: x.text, tags)
    except:
        tags = None
    return tags

def saveTags(pid, tags):
    with open(pid + '/tags.txt', 'wb') as f:
        tags = ','.join(tags)
        print '\ttags:' , tags
        f.write(tags)
        f.write('\n')

def scrollMoreSearchResults(driver, count):
    # wait until more search results are displayed
    images = []
    for i in range(settings.scrollTimeout):
        try:
            images = driver.find_elements_by_css_selector('a.pinImageWrapper div div img')
            if len(images) > count:
                break
        except:
            pass
        time.sleep(1)
    return images

def getSearchResults(driver):
    scrollJS = '''
                var c = document.getElementsByClassName("flashlightResultsContainer")[0];
                c.scrollTop = c.scrollHeight;
               '''
    results = []

    # retrieve seach results:
    count = 0
    retry = 0
    while count < settings.limit:
        images = scrollMoreSearchResults(driver, count)

        # no more search results
        if len(images) <= count:
            break

        offset = count
        for image in images[offset:]:
            count += 1
            if count > settings.limit:
                break
            try:
                src = image.get_attribute('src')
                src = re.sub(r'\d+x', 'originals', src)
                results.append(src)
            except:
                break

        if count < settings.limit:
            driver.execute_script(scrollJS)
            # wait for scroll interval
            if settings.scrollInterval:
                time.sleep(settings.scrollInterval)
        else:
            break
    return results

def saveSearchResults(pid, results):
    with open(pid + '/search-results.txt', 'wb') as f:
        for index, src in zip(range(1, len(results)+1), results):
            print "\t%5d: %s" % (index, src);
            f.write(src)
            f.write('\n')


if __name__ == '__main__':
    links = get_all_links()

    driver = create_driver()

    if not login(driver):
        print 'login failed, quit'
        driver.quit()
        exit(1)
    # wait for login to complete
    time.sleep(5)

    linkCount = len(links)
    for index, link in zip(range(1, linkCount+1), links):
        print '%d of %d, link: %s' % (index, linkCount, link)

        # visit page:
        try:
            driver.get(link + 'visual-search')
        except:
            print 'cannot load this link or timeout, quit'
            break

        # extract pin id
        pid = re.search(r'[0-9]+', link).group(0)
        # make directory for link
        if not os.path.exists(pid):
            os.mkdir(pid)

        # get and save source image
        src = getSource(driver)
        if not src:
            print 'cannot get source image, quit'
            break
        else:
            saveSource(pid, src)

        # get and save tags
        tags = getTags(driver)
        if not tags:
            print 'cannot get tags, quit'
            break
        else:
            saveTags(pid, tags)

        # get and save search results
        results = getSearchResults(driver)
        if not results:
            print 'cannot get search results, quit'
            break
        else:
            saveSearchResults(pid, results)

        # interval between two links, to avoid ban from Pinterest
        if settings.searchInterval:
            time.sleep(settings.searchInterval)

    driver.quit()
