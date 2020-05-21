import asyncio
from .patch_pyppeteer import patch_pyppeteer
patch_pyppeteer()
from pyppeteer import launcher, launch
from pyppeteer.errors import PageError
import os

from .utils import *
from .Course import Course

class Scraper(object):
    def __init__(self, WS = None, basedir=None, max_downloads = 5, poolsize = 5, loglevel=logging.INFO, cache=False, dup_files=True, base_url="https://canvas.mit.edu"): 
        if basedir is None:
            basedir = os.getcwd()
        self.basedir = basedir = pathjoin(basedir, "output")
        os.makedirs(self.basedir, exist_ok=True)
        self.log = config_logger(loglevel, basedir, repr(self))
        self.WS = WS
        self.max_downloads = max_downloads
        self.poolsize = poolsize
        self.dup_files = dup_files
        self.base_url = base_url

        self.do_cache = cache
        self.cache_path = pathjoin(basedir, "cache.jsn")
        if os.path.exists(self.cache_path):
            self.downloads_cache = read_json(self.cache_path)
        else:
            self.downloads_cache = dict()
            update_json(self.cache_path, self.downloads_cache)
        
        self.targetCreationLock = asyncio.Lock()
        self.studyNetLock = asyncio.Lock()
        self.downloads_cleanup()        

    def downloads_cleanup(self):
        downloads = self.get_downloads()
        if downloads:
            self.log.error("Incomplete download files found. cleaning up")
            #if prompt_y_n("Warning: %d downloads still pending. Clean up"%len(downloads)):
            for download in downloads:
                self.log.warning("deleting " + download)
                os.remove(download)          

    async def _go(self, amount=None, *course_nums):
        await self.init()
        await self.handle_login()
        #assert(prompt_y_n("finished_login"))
        await self.scrape_all_courses(amount, *course_nums)
        await self.scrape_all_studynet(amount, *course_nums)

    def go(self, amount=None, *course_nums):
        return go(self._go(amount, *course_nums))
        
    async def init(self):
        if self.WS: # connect to existing browser process
            browser = await launcher.connect(browserWSEndpoint=self.WS, defaultViewport=None)
            self.browser = browser
        
        else: # create new chromium process
            #args = [ '--start-maximized' ]
            args = [ '--window-size=1000,1000' ]
            browser = await launch(headless=False, defaultViewport=None, args=args)
            self.WS = browser.wsEndpoint
            self.browser = browser

        self.log.info(self.WS)

    async def handle_login(self):
        pages = await self.browser.pages()
        p = pages[0]
        await p.goto(self.base_url + "/courses")
        assert(prompt_y_n("Please login in the Chromium window. Finished_login"))



        

    async def scrape_all_courses(self, amount=None, *course_nums):
        self.downloads_cleanup()
        async with self.targetCreationLock:
            page = await self.browser.newPage()
        # open courses page
        
        await page.goto(self.base_url + "/courses")

        # get all courses links
        
        links = set([l["href"] for l in await get_all_links(page) if "/courses/" in l["href"]])

        if course_nums:    
            links = [l for l in links if any(str(num) in l for num in course_nums)]

        links = sorted(links)
        
        # create scraping tasks
        courses = [Course(link, self) for link in links][:amount]
        tasks = [c.go() for c in courses]

        # pool tasks
        curtasks = set()
        all_results = []
        results = []
        for task in tasks:
            if len(curtasks) >= self.poolsize:
                results, curtasks = await asyncio.wait(curtasks, return_when=asyncio.FIRST_COMPLETED)
                all_results += results
            curtasks.add(task)

        # await for lingering tasks
        results, curtasks = await asyncio.wait(curtasks) 
        all_results += results

        # await for lingering downloads
        i = 5
        while(self.count_downloads() > 0):
            self.log.info("Waiting for %d downloads to finish, sleeping for %ds"%(self.count_downloads(), i))
            await asyncio.sleep(i)
            i = min(60, i*2)


        # check for any failures
        if any(r.exception() for r in all_results):
            self.log.warning("Some tasks failed - restarting failed tasks")
            for r in all_results:
                if r.exception():
                    self.log.error(r.exception())
            await self.scrape_all_courses()
        elif any([c.db_cleanup_all() for c in courses]):
                self.log.warning("DB inconsistencies fixed - restarting failed tasks")
                await self.scrape_all_courses()
        else:
            self.log.info("Finished scraping all canvas files successfully")
            return True


    async def scrape_all_studynet(self, amount=None, *course_nums):
        page = (await self.browser.pages())[0]
        await page.goto(self.base_url + "/courses")

        # get all courses links
        links = set([l["href"] for l in await get_all_links(page) if "/courses/" in l["href"]])

        if course_nums:    
            links = [l for l in links if any(str(num) in l for num in course_nums)]

        links = sorted(links)
        
        # create scraping tasks
        courses = [Course(link, self) for link in links][:amount]
        tasks = [c.go2() for c in courses]

        for link in links[:amount]:
            while True:
                course = Course(link, self)
                try:
                    await course.go2()
                except Exception as e:
                    self.log.error("Error downloading Study.Net for %s, retrying"%link)
                    self.log.error(e)

                else:
                    break
            
        # await for lingering downloads
        i = 5
        while(self.count_downloads() > 0):
            self.log.info("Waiting for %d downloads to finish, sleeping for %ds"%(self.count_downloads(), i))
            await asyncio.sleep(i)
            i = min(60, i*2)

        self.log.info("Finished scraping all Study.Net successfully")
        return True
   
    def get_downloads(self):
        return [str(x) for x in Path(self.basedir).rglob("*.crdownload")]

    def count_downloads(self):
        return len(self.get_downloads())

    async def await_downloads_cap(self):
        i = 5
        while(self.count_downloads() >= self.max_downloads):
            self.log.debug("Max Download Exceeded, sleeping for %ds"%i)
            await asyncio.sleep(i)
            i = min(60, i*2)


    async def download(self, page, url, path):
        if self.do_cache and url in self.downloads_cache:
            if self.downloads_cache[url] == path:
                # cached file was previously not downloaded successfully / has been removed, redownload
                self.log.warning("Re-downloading cached file from %s to %s"%(url, path))
            else:
                self.log.debug("File already in cache: %s is in %s"%(url, self.downloads_cache[url]))
                name = find_free_name(path, "DUP", "txt")
                with open(pathjoin(path, name), "w") as f:
                    f.write("{URL}\nwas previously downloaded to\n{location}".format(URL=url,location=self.downloads_cache[url]))
                return
        
        self.downloads_cache[url] = path
        update_json(self.cache_path, self.downloads_cache)

        await self.await_downloads_cap()

        await set_page_download_folder(page, path)        

        try:
            await page.goto(url)
            # if we get here, the download didn't start. likely a locked file save the page
            with open(pathjoin(path, (await page.title()) + ".html"), "w") as f:
                f.write(await get_body(page))

        except PageError: # this means we started downloading
            return

def run_scrape(**conf):
    s = Scraper(**conf)
    s.go()
    return s
