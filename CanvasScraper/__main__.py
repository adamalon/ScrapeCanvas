from .Scraper import Scraper, run_scrape

import logging
import argparse
text = 'Canvas Scraper v1.0'
parser = argparse.ArgumentParser(description=text)
parser.add_argument("--dir", "-d", help="set output directory (default: CWD)", default=None)
parser.add_argument("--WS", help="set WS address (default: None)", default=None)
parser.add_argument("--max_downloads", help="set maximum concurrent downloads (default: 5)", default=5, type=int)
parser.add_argument("--poolsize", help="set maximum operating threads (default: 5)", default=5, type=int)
parser.add_argument("--loglevel", help="set logging level (default: 20(INFO))", default=logging.INFO, type=int)
parser.add_argument("--cache", help="If 1: does not download duplicate files (default: 0)", default=False, type=bool)
parser.add_argument("--files", help="If 1: does not download individual files if 'files' module exists for course (default: 1)", default=True, type=bool)
parser.add_argument("--url", "-u", help="Canvas URL (default: https://canvas.mit.edu)", default="https://canvas.mit.edu")

args = parser.parse_args()

if __name__ == "__main__":
    run_scrape(WS = args.WS,
               basedir = args.dir,
               max_downloads = args.max_downloads,
               poolsize = args.poolsize,
               loglevel = args.loglevel,
               cache = args.cache,
               dup_files = not args.files,
               base_url = args.url)

