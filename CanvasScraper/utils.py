import asyncio
import logging
import os
import json
from pathlib import Path
import glob

whitelist = "0123456789:+.()'?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]_-abcdefghijklmnopqrstuvwxyz "
sanitable = [chr(i) if chr(i) in whitelist else "%"+"%02x"%i for i in range(256)]
sanitable[ord(":")] = "-"


def sanitize(s, table=sanitable):
    return s.translate(sanitable)

def config_logger(loglevel, basedir, logname):        
    logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
    rootLogger = logging.getLogger(logname)
#    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.DEBUG) # capture DEBUG level

    fileHandler = logging.FileHandler(os.path.join(basedir, 'log.log'))
    fileHandler.setFormatter(logFormatter)
    fileHandler.setLevel(logging.DEBUG) # record DEBUG level to file
    rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    consoleHandler.setLevel(loglevel) # record given level to console
    rootLogger.addHandler(consoleHandler)

    return rootLogger 

def pathjoin(base, *paths):
    return os.path.join(base, *map(sanitize, paths))

def update_json(path, db):
    with open(path, 'w') as f:
        json.dump(db, f, indent=4)

def read_json(path):
    with open(path, 'r') as f:
        return json.load(f)
        
async def get_body(page):
    body =  await page.evaluate("document.documentElement.outerHTML", force_expr=True)
    return body
    
async def map_over_template(page, template, tags):
    res = []
    length =  await page.evaluate('%s.length'%template, force_expr=True)
    for i in range(length):
        res.append({tag: (await page.evaluate('%s[%s].%s'%(template,i,tag), force_expr=True)).strip() for tag in tags})
    return res

async def get_links_by_classname(page, classname, timeout=10):
    template = 'document.getElementsByClassName("%s")'%classname
    for i in range(timeout):
        if await page.querySelectorAll('[class="%s"]'%classname):
            break
        await asyncio.sleep(1)
        #await page.waitFor('[class="%s"]'%classname, timeout=timeout)

    return await map_over_template(page, template, ['href', 'textContent'])

async def get_all_links(page):
    template = 'document.getElementsByTagName("a")'
    return await map_over_template(page, template, ['href', 'textContent'])    
    
def prompt_y_n(prompt):
    v = None
    while v not in ["y","yes", "n", "no"]:
        v = input(prompt.strip()+" (y/n)? ").strip().lower()
    return v in ["y", "yes"]

def prompt_y(prompt):
    while not prompt_y_n(prompt):
        pass

async def set_page_download_folder(page, path):
    sess = await page.target.createCDPSession()
    await sess.send('Page.setDownloadBehavior', {'behavior': 'allow', 'downloadPath': path})


def find_free_name(path, basename, suffix, template="{basename} ({i}).{suffix}"):
    i = 0
    name = basename
    while os.path.exists(os.path.join(path, name)):
        i += 1
        name = "{basename} ({i}).{suffix}".format(basename=basename,
                                                  i=i,
                                                  suffix=suffix)
    return name
    

def go(f):
    return asyncio.get_event_loop().run_until_complete(f)
