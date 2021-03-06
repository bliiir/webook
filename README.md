# webook (Webpage to EBook) #
framework for parsing a webpage into an ePUB


## Install Instructions ##

```
git clone https://github.com/jancr/webook.git
cd webook
pip3 install setup.py
```

If you only want to use the tool from the command line:

```
pip3 install setup.py --no-flask
```

If you only want to use the web server interface:

```
pip3 install setup.py --no-tqdm
```


## Dependencies ##
Dependencies are installed by setup.py, but if you want to install them manually:

**[Python 3](https://www.python.org/downloads/) and packages**

**lxml (requred)**

* `pip install lxml`

**BeautifullSoap (requred)**

   * `pip3 install beautifulsoup4`


**Flask (optional)**

* `pip3 install flask`


**tqdm (optional)**

* `pip3 install qtdm`


## How To Use ##

The tool itself is a python script with a command line interface.

Or

as a Flask web App

### Flask Webserver ###

```
webook --webserver
```

Point browser to http://localhost:5555 or 0.0.0.0:5555

### Comand-line ###

```
$ webook -h
usage: webook [-h] [--title TITLE] url book_file

positional arguments:
  url            url to where the book is located, fx
                 https://www.fanfiction.net/s/9658524/1/Branches-on-the-Tree-
                 of-Time
  book_file      the file name of final book

optional arguments:
  -h, --help     show this help message and exit
  --title TITLE  The title of the book, default name is scraped from the
                 website
```

Example:

```
webook www.fanfiction.net/s/9658524/1/Branches-on-the-Tree-of-Time \ 
		time.epub
````

* Website is the url of the site you want to scrape
* book_file is the file name of the book you produce, default book.epub
* title of the book, by default it is scraped from the website

## Developer Notes ##

For each type of webpage there is a corresponding file and class in the `webook/modules` folder.
Initially I strive to be able to parser books from fanfiction.net (**DONE**) such as:

* https://www.fanfiction.net/s/9658524/1/Branches-on-the-Tree-of-Time

'Generic' wordpress blogs (**TODO**) such as 

* https://parahumans.wordpress.com/

### Code Structure ###

The Base Idea is that for each book type, the base skeleton of will be available
under `book_templates`, for now only epub is available, yes an epub file is
basically xhtml + xml. Not scary at all :)

```
$ ll book_templates/epub
drwxr-xr-x@ 3 jcr  staff    96B Jun  4 23:19 META-INF
-rwxr-xr-x  1 jcr  staff   934B Nov 22 12:23 content.opf
-rwxr-xr-x@ 1 jcr  staff    20B Jun  4 23:19 mimetype
-rwxr-xr-x@ 1 jcr  staff    50B Jun  4 23:19 page_style.css
-rwxr-xr-x@ 1 jcr  staff   404B Jun  4 23:19 page_template.xhtml
-rwxr-xr-x@ 1 jcr  staff   248B Jun  4 23:19 stylesheet.css
-rwxr-xr-x@ 1 jcr  staff   670B Jun  4 23:19 titlepage.xhtml
-rwxr-xr-x  1 jcr  staff   578B Nov 22 17:40 toc.ncx
```

`webook/webook.py` contains the heart of the project. It contains the class `EBook`
which contains all the code necessary for creating an ebook. It has a fairly
simple API, In order to make it work, one must subclass it and 'teach' it to
parse your favorite websites. This is done by overwriting the abstract `parse` method in
the child classes, and by calling `update` for each chapter/section of the
book.

While it may sound very scary to subclass EBook, the parser for parsing
`www.fanfiction.net/` (`FanFictionEBook`) is less than 30 lines of code. To
read the code for inspiration, see `webook/modules/fanfiction.py`

**TLDR**

* look under `webook/modules` for inspiration to create your own parsers
* `book_templates/epup` and `webook/webook.py` contains all the secret sauce.


