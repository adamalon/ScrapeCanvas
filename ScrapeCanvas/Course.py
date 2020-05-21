import asyncio
import pyppeteer.errors
from .utils import *

class Course(object):
    def __init__(self, URL, context):
        self.URL = URL
        self.context = context
        self.log = context.log
        self.no_files_tab = None
        
    def db_cleanup_all(self):
        return any([self.db_cleanup(tree_name) for tree_name in ["modules", "assignments", "announcements"]])

    def db_cleanup(self, tree_name):
        ret = False
        tree_dir = pathjoin(self.dir, tree_name)
        tree_info_path = pathjoin(tree_dir, "tree_info.jsn")

        if os.path.exists(tree_info_path):
            tree_info = read_json(tree_info_path)
            for leaf in tree_info.values():
                leaf_dir = pathjoin(tree_dir, leaf["name"])
                leaf_info_path = pathjoin(leaf_dir, "leaf_info.jsn")
                if os.path.exists(leaf_info_path):
                    leaf_info = read_json(leaf_info_path)
                    dirlist = [fname for fname in os.listdir(leaf_dir) if fname not in ['leaf_info.jsn', 'body.html', '.DS_Store']]
                    if len(dirlist) != len(leaf_info)-1:
                        ret = True
                        self.log.warning("Inconsistent DB at %s, cleaning up" % leaf_dir)
                        # removing all files from folder
                        for fpath in os.listdir(leaf_dir):
                            os.remove(os.path.join(leaf_dir, fpath))
                        tree_info[leaf_info["leaf"]["href"]]["done"] = False            
            update_json(tree_info_path, tree_info)
        return ret

    async def go(self):
        await self.init()
        await self.download_all_files()
        await self.download_all_modules()
        await self.download_all_assignments()
        await self.download_all_announcements()
        #await self.download_study_net()
        await self.page.close()
        self.log.info("Finished scraping %s" % self.title)


    async def go2(self):
        await self.init()
        await self.download_study_net()
        await self.page.close()
        self.log.info("Finished Study.Net for %s" % self.title)


    async def init(self):
        async with self.context.targetCreationLock:
            self.page = await self.context.browser.newPage()
        await self.page.goto(self.URL)
        title = await self.page.title()

        course_info_path = pathjoin(self.context.basedir, title, "course_info.jsn")

        i=0        
        while os.path.exists(course_info_path):
            course_info = read_json(course_info_path)
            if self.URL == course_info["URL"]: # found existing match
                self.log.info("Continuing " + title)
                self.title = course_info['title']
                self.dir = course_info['dir']
                break
            else:
                self.log.info("Duplicte course: " + title) # found "fake" match, continuing
                i+= 1
                title = "%s (%s)"%(title, i)
                course_info_path = pathjoin(self.context.basedir, title, "course_info.jsn")
        else:
            self.log.info("Starting " + title) # no match; new course
            self.title = title
            self.dir = pathjoin(self.context.basedir, self.title)
            os.makedirs(self.dir, exist_ok=True)
            course_info = {"URL": self.URL, "title": self.title, "dir": self.dir}
            course_info_path = pathjoin(self.dir, "course_info.jsn")
            update_json(course_info_path, course_info)

        self.course_info_path = course_info_path
        with open(pathjoin(self.dir, "body.html"), "w") as f:
            f.write(await get_body(self.page))

    async def download_all_assignments(self):
        return await self.download_tree(tree_name="assignments", lnk_gen=get_links_by_classname(self.page, "ig-title"))
        
    async def download_all_modules(self):
        return await self.download_tree(tree_name="modules", lnk_gen=get_links_by_classname(self.page, "ig-title title item_link"))

    async def download_all_announcements(self):
        return await self.download_tree(tree_name="announcements", lnk_gen=get_links_by_classname(self.page, "ic-item-row__content-link"))


    async def download_tree(self, tree_name, lnk_gen):
        tree_dir = pathjoin(self.dir, tree_name)
        tree_info_path = pathjoin(tree_dir, "tree_info.jsn")

        if os.path.exists(tree_info_path):
            self.log.debug("Resuming %s for course %s" % (tree_name, self.title))
        else:
            await self.page.goto(self.URL + "/" + tree_name)
            
            if self.page.url == self.URL and tree_name != "modules": # was redirected back to main -- could not find tab (modules is the only exception)
                self.log.debug("Could not locate %s tab for course %s" % (tree_name, self.title))
                lnk_gen.close()
                return

            self.log.debug("Starting %s for course %s" % (tree_name, self.title))    
            os.makedirs(tree_dir, exist_ok=True)
        
        self.db_cleanup(tree_name)

        if os.path.exists(tree_info_path):
            tree_info = read_json(tree_info_path)
            lnk_gen.close()
        else:
            tree_info = {}
            lnks = await lnk_gen
            for i, lnk in enumerate(lnks):
                if lnk["href"] in tree_info:
                    continue
                entry = {}
                entry["done"] = False
                entry["name"] = "%d - %s"%(i, lnk['textContent'])
                entry["href"] = lnk["href"]
                entry["textContent"] = lnk["textContent"]
                tree_info[entry["href"]] = entry # index by href
            update_json(tree_info_path, tree_info)

        for leaf in tree_info.values():
            if leaf["done"]:
                continue
            try:
                await self.download_leaf(leaf, tree_dir, tree_name)
                leaf["done"] = True
            except pyppeteer.errors.TimeoutError:
                self.log.error("Error downloading %s"%leaf["href"])
                continue 
            update_json(tree_info_path, tree_info)

        self.log.debug("Finished %s for %s"%(tree_name, self.title))

    async def download_leaf(self, leaf, tree_dir, tree_name):
        self.log.debug("Downloading %s: %s | %s"%(tree_name, self.title, leaf["name"]))


        leaf_dir = pathjoin(tree_dir, leaf["name"]) 
        os.makedirs(leaf_dir, exist_ok=True)
        
        await self.page.goto(leaf['href'])

        with open(pathjoin(leaf_dir, "body.html"), "w") as f:
            f.write(await get_body(self.page))

        leaf_info_path = pathjoin(leaf_dir, "leaf_info.jsn")
        
        if os.path.exists(leaf_info_path):
            leaf_info = read_json(leaf_info_path)
        else:
            leaf_info = {}
        
        
        lnks = [l for l in await get_all_links(self.page) if ("/download?" in l['href']) and l['textContent']]

        # better to do this after, so we wait until the page was loaded to avoid warnings
        if self.no_files_tab == False and not self.context.dup_files:
            lnks = []

        
        for lnk in lnks:
            if lnk["href"] in leaf_info:
                continue
            entry = {}
            entry["done"] = False
            entry["href"] = lnk["href"]
            entry["textContent"] = lnk["textContent"]
            
            leaf_info[entry["href"]] = entry # index by href

        leaf_info["leaf"] = leaf
        update_json(leaf_info_path, leaf_info)
        for entry in leaf_info.values():
            if entry == leaf:
                continue
            if entry['done']:
                continue
            self.log.debug("Downloading %s: %s | %s | %s"%(tree_name, self.title, leaf["name"], entry['textContent']))
            
            await self.context.download(self.page, entry['href'], leaf_dir)

            entry['done'] = True
            update_json(leaf_info_path, leaf_info)

    async def download_all_files(self):
        files_dir = pathjoin(self.dir, "files")
        
        if os.path.exists(pathjoin(files_dir, "course_files_export.zip")):
            self.log.debug("Found previous file export for course %s" % self.title)
            self.no_files_tab = False
            return

        await self.page.goto(self.URL + "/files")       
        if self.page.url == self.URL: # was redirected back to main -- could not find files tab
            self.log.debug("Could not locate files tab for course %s" % (self.title))
            self.no_files_tab = True
            return

        self.log.debug("Starting files tab for course %s" % self.title)

        self.no_files_tab = False
        os.makedirs(files_dir, exist_ok=True)
        async with self.context.targetCreationLock:
            await self.page.bringToFront()
            #await self.page.waitForSelector('[class="grid-row ef-quota-usage"]')
            await self.page.waitForSelector('[class="ef-item-row"]')
            await self.page.click('[class="ef-item-row"]')
            await self.page.keyboard.down('Control')
            await self.page.keyboard.press('KeyA')
            await self.page.keyboard.up('Control')
            button = await self.page.querySelector('[class="ui-button btn-download"]')

            await set_page_download_folder(self.page, files_dir)
            await self.context.await_downloads_cap()
            
            await button.click()
            self.log.debug("Initiating zip for course %s" % self.title)
            await self.page.waitForSelector('[class="alert alert-info"]')
            self.log.debug("Prepping zip for course %s" % self.title)
        while await self.page.querySelectorAll('[class="alert alert-info"]'):        
            await asyncio.sleep(1)
        self.log.debug("Downloading zip for course %s" % self.title)

    # NOT THREADSAFE
    async def download_study_net(self):
        study_dir = pathjoin(self.dir, "Study.Net Materials")
        
        if glob.glob(os.path.join(study_dir, "*.zip")):
            self.log.debug("Found previous Study.Net export for course %s" % self.title)
            return

        if os.path.exists(pathjoin(study_dir, "resp.html")):
            self.log.debug("Found previous Study.Net response for course %s" % self.title)
            return


        await self.page.goto(self.URL + "/external_tools/166")       
        if self.page.url == self.URL: # was redirected back to main -- could not find files tab
            self.log.debug("Could not locate Study.Net tab for course %s" % (self.title))
            return


        self.log.debug("Starting Study.Net tab for course %s" % self.title)
        
        os.makedirs(study_dir, exist_ok=True)

        # Study.Net does not seem to handle multisessions well, so we lock here
        async with self.context.targetCreationLock:
            await self.page.bringToFront()
            for i in range(10):
                if any([f.url == "https://www.study.net/api/lti/default_vs.asp" for f in self.page.frames]):
                    break
                await asyncio.sleep(1)
            else:
                raise TimeoutError("Timeout in openning Study.Net tab")

            frames = [f for f in self.page.frames if f.url == "https://www.study.net/api/lti/default_vs.asp"]
            if len(frames) != 1:
                raise KeyError("Ambigous Study.Net frame count - found %d frames"%len(frames))

            frame = frames[0]
            self.log.debug("Study.Net frame located succesfully for %s" % self.title)

            for i in range(10):
                if await frame.querySelector('[name="chk_all"]'):
                    break

                body = await get_body(frame)
                
                if "the referenced course does not exist" in body:
                    self.log.debug("No Study.Net materials for %s" % self.title)
                    with open(pathjoin(study_dir, "resp.html"), "w") as f:
                        f.write(await get_body(frame))
                    return

                if "This course has expired" in body:
                    self.log.debug("Study.Net materials have expired for %s" % self.title)
                    with open(pathjoin(study_dir, "resp.html"), "w") as f:
                        f.write(await get_body(frame))

                    return

                await asyncio.sleep(1)
            else:
                raise TimeoutError("Unknown Study.Net error for %s" % self.title)

            await frame.waitForSelector('[name="chk_all"]')
            await asyncio.sleep(2) # just to be safe?
            await frame.click('[name="chk_all"]')
            self.log.debug("Study.Net 'check all' clicked succesfully for %s" % self.title)

            # WARNING: RACE CONDITION
            # If between creating the listener and  clicking the button some other
            # 'targetcreated' event happens, we will get the wrong page.
            # The targetCreationLock mutex promises no other pages are created concurrently.
#            async with self.context.targetCreationLock:
            result_page_future = asyncio.get_event_loop().create_future()
            self.page.browser.once('targetcreated', lambda target: result_page_future.set_result(target))
            await frame.click('[id="btnSubmit"]')
            self.log.debug("Study.Net download button clicked for %s" % self.title)

            popup = await (await result_page_future).page()
            
            await set_page_download_folder(popup, study_dir)
            await popup.waitForSelector('[href="down_zip.asp"]', timeout=60000) # wait up to 1 minute
            await popup.click('[href="down_zip.asp"]')
            await popup.close()
            
        self.log.debug("Study.Net dowload triggered succesfully for %s" % self.title)
        


        
