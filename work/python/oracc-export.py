#!/usr/bin/env python
"""Export cuneiform corpus from ORACC
"""

import sys
import os
import argparse
import logging
import json
import re
import shutil
from selenium import webdriver
from selenium.webdriver.remote import webelement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException


ORACC_SITES = ['http://oracc.org', 'http://oracc.museum.upenn.edu']
RE_CUNEIFORM_HREF = re.compile(r'javascript:cuneifyPopup\(\'([\w/]+)\',\'(\w+)\'\)')
RE_REPLACE_ANNOTATION = re.compile(r'[\[\]A-Za-z0-9#⸢⸣?]+')
RE_NON_EMPTY = re.compile(r'\S+')
XPATH_CUNEIFY_LINES = \
    '//table[@class="cuneify-text"]/tbody/tr[contains(@class, "cuneify-line")]/td/p[@class="cuneify-content"]'
EXPORTED_FILES = set()


def wait_for_xpath(wd: webdriver, xpath: str, timeout=10):
    WebDriverWait(wd, timeout).until((EC.presence_of_element_located((By.XPATH, xpath))))


def store_cuneiform(args: argparse.Namespace, lines: list, corpus_name: str, object_name: str):
    if not args.annotations:
        mangled = [RE_REPLACE_ANNOTATION.sub('', line) for line in lines]
        lines = mangled
    contents = '\n'.join(lines)
    if not RE_NON_EMPTY.search(contents):
        return
    # Write cuneiform characters into file
    dirname = os.path.join(args.directory, corpus_name.replace('/', os.path.sep))
    if not os.path.exists(dirname):
        os.makedirs(dirname, 0o755)
    filename = os.path.join(dirname, '{}.txt'.format(object_name))
    with open(filename, 'w', encoding='utf-8') as f:
        print(contents, file=f)
    if args.corpus_file:
        EXPORTED_FILES.add(filename)


def extract_cuneiform(args: argparse.Namespace, wd: webdriver, cuneified_link: webelement, window_handles: list):
    corpus_name, object_name = RE_CUNEIFORM_HREF.match(cuneified_link.get_attribute('href')).groups()
    cuneified_link.click()
    if wd.name == 'firefox':
        WebDriverWait(wd, 10).until(EC.new_window_is_opened(window_handles))
    wd.switch_to.window('cuneified')
    # Workaround to ensure that the cuneify-text table exists
    try:
        wait_for_xpath(wd, '//table[@class="cuneify-text"]')
    except TimeoutException:
        try:
            wd.find_element_by_xpath('//table[@class="cuneify-text"]/tbody')
        except NoSuchElementException:
            wd.close()
            return
    cuneiform_lines = [line.text for line in wd.find_elements_by_xpath(XPATH_CUNEIFY_LINES)]
    store_cuneiform(args, cuneiform_lines, corpus_name, object_name)
    wd.close()


def export_corpus(args: argparse.Namespace, wd: webdriver, name: str, oracc_site=ORACC_SITES[0]):
    logging.info('Opening corpus {}'.format(name))
    wd.get('{0}/{1}/{2}'.format(oracc_site, name, 'corpus'))
    xpath_designations_table = '//div[@id="p3right"]/table[@class="xmd"]'
    try:
        wd.find_element_by_xpath(xpath_designations_table)
    except NoSuchElementException:
        logging.warning('No objects found in the corpus {}'.format(name))
        return
    # Save all object link texts, as we go to object pages and back to object list
    object_link_texts = [link.text for link in wd.find_elements_by_xpath('//tr[not(@class)]/td[2]/a')]
    logging.debug('Found {} objects'.format(len(object_link_texts)))
    for object_link_text in object_link_texts:
        # Open object page
        object_link = wd.find_element_by_link_text(object_link_text)
        object_link.click()
        xpath_outline_panel = '//div[contains(@class, "xmdoutline")]'
        wait_for_xpath(wd, xpath_outline_panel)
        xpath_object_numbers_name = '//div[contains(@class, "xmdoutline")]/h3[text()="Numbers"]/following::ul[1]/li[2]'
        logging.info('Processing object {}'.format(wd.find_element_by_xpath(xpath_object_numbers_name).text))
        # Prepare for switching windows
        window_handles = wd.window_handles
        oracc_window_handle = wd.current_window_handle
        # Search for Cuneified link
        try:
            # Open Cuneified link and process text
            cuneified_link = wd.find_element_by_link_text('Cuneified')
            extract_cuneiform(args, wd, cuneified_link, window_handles)
        except NoSuchElementException:
            pass
        # Return to original window
        wd.switch_to.window(oracc_window_handle)
        # Go back
        wd.back()
        wait_for_xpath(wd, xpath_designations_table)


def export_all(args: argparse.Namespace, oracc_site=ORACC_SITES[0]):
    # Initialise webdriver
    if args.browser == 'firefox':
        wd = webdriver.Firefox()
    elif args.browser == 'phantomjs':
        wd = webdriver.PhantomJS()
    else:
        raise NotImplementedError('Software not tested with browser {}'.format(args.browser))
    # Get list of projects
    logging.info('Getting list of projects')
    wd.get('{0}/{1}'.format(oracc_site, 'projects.json'))
    if wd.name == 'firefox':
        # Click raw data button to switch to raw data view
        xpath_raw_data_button = '//a[@id="tab-1"]'
        wait_for_xpath(wd, xpath_raw_data_button)
        wd.find_element_by_xpath(xpath_raw_data_button).click()
        # Get raw data
        xpath_projects_data = '//pre[@class="data"]'
        wait_for_xpath(wd, xpath_projects_data)
        projects = json.loads(wd.find_element_by_xpath(xpath_projects_data).text)
    else:
        # Get raw data from the body text
        projects = json.loads(wd.find_element_by_tag_name('body').text)
    if args.starting:
        starting_index = projects['public'].index(args.starting)
        if starting_index:
            del projects['public'][0:starting_index]
    for project_name in projects['public']:
        if args.corpora and project_name in args.corpora or not args.corpora:
            export_corpus(args, wd, project_name, oracc_site)
    wd.quit()
    if args.corpus_file:
        logging.info('Creating corpus file {}...'.format(args.corpus_file))
        with open(args.corpus_file, 'w', encoding='utf-8') as corpus:
            for exported_file in sorted(EXPORTED_FILES):
                logging.debug('Processing {}...'.format(exported_file))
                with open(exported_file, 'r', encoding='utf-8') as inp:
                    shutil.copyfileobj(inp, corpus)
                    print('', file=corpus)  # add newline at the end of every file


def main():
    argparser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__)
    argparser.add_argument('-d', '--directory', help='Output directory', default=os.getcwd())
    argparser.add_argument('-a', '--annotations', help='Do not remove annotations')
    argparser.add_argument('-c', '--corpora', help='Download only these corpora')
    argparser.add_argument('-s', '--starting', help='Starting corpus')
    argparser.add_argument('-f', '--corpus_file', help='Specify corpus file')
    argparser.add_argument('-b', '--browser', choices=['firefox', 'phantomjs'], default='firefox',
                           help='Browser to use for accessing ORACC')
    args = argparser.parse_args()
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO)
    export_all(args)


if __name__ == '__main__':
    main()
