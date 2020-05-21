from distutils.core import setup

setup(
  name = 'ScrapeCanvas',         # How you named your package folder
  packages = ['ScrapeCanvas'],   # Chose the same as "name"
  version = '1.2',      # Start with a small number and increase it with every change you make
  license='gpl-3.0',        # Chose a license from here: https://help.github.com/articles/licensing-a-repository
  description = 'Python Scraper for Canvas',   # Give a short description about your library
  author = 'Adam Alon',                   # Type in your name
  author_email = 'adamalonil+canvasscraper@gmail.com',      # Type in your E-Mail
  url = 'https://github.com/adamalon/CanvasScraper',   # Provide either the link to your github or to your website
  download_url = 'https://github.com/adamalon/CanvasScraper/archive/v1.2.tar.gz',    # I explain this later on
  keywords = ['Canvas', 'Scraper', 'MIT', 'ScrapeCanvas'],   # Keywords that define your package best
  install_requires=[            
          'pyppeteer',
          'certifi',
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers',      # Define that your audience are developers
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',   # Again, pick a license
    'Programming Language :: Python :: 3',      #Specify which pyhton versions that you want to support
  ],
)
