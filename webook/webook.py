
# core imports
import os
from os.path import join as pjoin
import shutil
import urllib
import urllib.request
import urllib.parse
import xml.etree.cElementTree as ET
from xml.dom import minidom
import argparse
import tempfile
import uuid
from distutils.dir_util import copy_tree

# 3rd party imports
import bs4
from bs4 import BeautifulSoup as Soup

################################################################################
# Globals
################################################################################
# WEBSITE = 'http://shinsekai.cadet-nine.org/'
ROOT = pjoin(os.path.split(os.path.abspath(__file__))[0], '..')
soup = Soup('', 'lxml')
TEMPLATE_FOLDER = pjoin(ROOT, "book_templates/epub")


################################################################################
# EBook Class
################################################################################
class EBook:
    TEMPLATE_FOLDER = pjoin(ROOT, "book_templates/epub")
    """An ebook basically consists of a bunsh of html files usually one pr chapter
    and a table of content that describes the relationship between the chapters"""

    def __init__(self, url, epup_file='book.epup', title=None):
        if not url.startswith('http'):
            url = f'http://{url}'
        self.toc_dict = {}
        with tempfile.TemporaryDirectory() as self.output_dir:
            copy_tree(pjoin(self.TEMPLATE_FOLDER), self.output_dir)

            self.ns = 'http://www.daisy.org/z3986/2005/ncx/'
            ET.register_namespace('', self.ns)
            self.toc_path = self.get_path("toc.ncx")
            self.toc = ET.parse(open(self.toc_path)).getroot()
            # self.nav_point_root = self.toc.find(f'{{{self.ns}}}navMap/{{{self.ns}}}navPoint')
            self.nav_point_root = self.toc.find(f'{{{self.ns}}}navMap')
            self.current_nav_point = self.nav_point_root
            self.play_order = 1

            self.content_path = self.get_path("content.opf")
            self.content = Soup(open(self.content_path), 'html.parser')
            self.content_manifest_tag = self.content.find('manifest')
            self.content_spine_tag = self.content.find('spine')

            ## TODO: parse notes and other optional stuff
            # variables expected to be scraped by self.scrape
            self.title = None
            self.first_name = None
            self.last_name = None
            self.cover_path = None

            # self.update('titlepage', self.title)
            self.scrape(url)

            if self.first_name:
                self.update_author(self.first_name, self.last_name)

            if title:
                self.title = title
            self.update_title(self.title)

            self.add_cover(self.cover_path)

            self.save(epup_file)


    def update_title(self, title):
        self.toc.find(f'{{{self.ns}}}docTitle/{{{self.ns}}}text').text = title
        self.nav_point_root.find(f'{{{self.ns}}}navPoint/{{{self.ns}}}navLabel/{{{self.ns}}}text').text = title
        self.content.find('package').find('metadata').find('dc:title').string = title

    def update_author(self, first_name, last_name=None):
        creator = self.content.find('package').find('metadata').find('dc:creator')
        if last_name is None:
            creator.string = first_name
            creator.attrs['opf:file-as'] = first_name
        elif first_name is not None:
            creator.string = f"{first_name} {last_name}"
            creator.attrs['opf:file-as'] = f"{first_name}, {last_name}"

    def add_cover(self, cover_path):
        # TODO jpg hardcoded, should alter files accordingly if not jpg!
        if cover_path is None:
            cover_path = 'https://vignette.wikia.nocookie.net/uncyclopedia/images/c/cf/Trollface.jpg'
        urllib.request.urlretrieve(cover_path, self.get_path('cover.jpg'))

    def update(self, name, heading, parent=None):
        """ updates content and table of content, needs to be called
        by scrape to add chapters, sections ect. to TOC
        """
        # if parent=None, then use last parent
        if parent is not None:
            self.current_nav_point = parent

        # update table of content
        self.play_order += 1
        args = {"id" : f"navPoint-{self.play_order}", "playOrder" : str(self.play_order)}
        elm = ET.SubElement(self.current_nav_point, "navPoint", **args)
        nav_label = ET.SubElement(elm, "navLabel")
        ET.SubElement(nav_label, "text").text = heading
        ET.SubElement(elm, "content", src="{}.xhtml".format(name))
        self.toc_dict[name] = elm

        # update content
        args={'href' : "{}.xhtml".format(name), 'id' : name, 'media-type' : "application/xhtml+xml"}
        self._append_soup_tag(self.content_manifest_tag, "item", args=args)
        self._append_soup_tag(self.content_spine_tag, 'itemref', args={'idref' : name})

    def save(self, epup_file):
        open(self.content_path, 'w').write(self.content.prettify())
        # et_to_file(self.toc, self.toc_path)
        with open(self.toc_path, 'w') as toc_file:
            toc_file.write('<?xml version="1.0" encoding="UTF-8" standalone="no" ?>\n')
            toc_file.write('<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN"\n')
            toc_file.write('"http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">\n\n')
            rough_string = ET.tostring(self.toc, encoding='unicode')
            rough_string = ''.join(map(str.strip, rough_string.split('\n')))
            toc_file.write(minidom.parseString(rough_string).toprettyxml("  "))
        os.unlink(self.get_path('page_template.xhtml'))

        # zip output_folder and rename it tou epup_file
        tmp_file_name = str(uuid.uuid4())[:10]
        shutil.make_archive(tmp_file_name, 'zip', self.output_dir)
        os.rename(f'{tmp_file_name}.zip', epup_file)

    def get_path(self, *path):
        return pjoin(self.output_dir, *path)

    def _append_soup_tag(self, target, name, text='', args=None):
        if args is None:
            args = {}
        _tag = soup.new_tag(name, **args)
        if text:
            _tag.string = text
        target.append(_tag)

    def write_chapter(self, chapter_tags, n_chapter, chapter_name=None):
        if chapter_name is None:
            chapter_name = f"Chapter {n_chapter}"
        chapter_file = open(self.get_path(f'chapter_{n_chapter}.xhtml'), 'w')

        chapter_soup = Soup(open(self.get_path('page_template.xhtml')), 'lxml')
        body_tag = chapter_soup.find('body')
        self._append_soup_tag(body_tag, "h3", chapter_name)
        if isinstance(chapter_tags, str):
            body_tag.append(soup.new_tag('div', chapter_tags))
        elif isinstance(chapter_tags, bs4.element.ResultSet):
            for tag in chapter_tags:
                body_tag.append(tag)
        elif isinstance(chapter_tags, bs4.element.Tag):
            body_tag.append(chapter_tags)
        else:
            raise ValueError("chapter_tag must be either string, bs4.element.Tag or bs4.element.ResultSet")
        chapter_file.write(chapter_soup.prettify())

    # the parse functions arbstract functions, that needs to be in the subclass
    def scrape(self, url):
        pass
