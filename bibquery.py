#!/usr/bin/env PYTHONIOENCODING=UTF-8 /usr/local/bin/python3
# encoding: utf-8
from __future__ import unicode_literals

import re
import sys
import urllib
import plistlib
import os.path
import subprocess
import json

from workflow import Workflow
import ccl_bplist

HOME = os.path.expanduser("~")
BIB_DIR = HOME + "/Library/Caches/Metadata/edu.ucsd.cs.mmccrack.bibdesk/"

def querify(query):
    """Return `query` as list"""
    if ' ' in query:
        queries = query.split(' ')
    else:
        queries = [query]
    return queries

################################################
# Convert `dict` to string
################################################

def _get_datum(_dict, key):
    """Get value from key"""
    try:
        if _dict[key] != []:
            if key == 'kMDItemAuthors':
                names = [x.split(', ') for x in _dict[key]]
                _res = [n[0] for n in names]
            elif key == 'net_sourceforge_bibdesk_publicationdate':
                year = str(_dict[key]).split('-')[0]
                _res = [year]
            else:
                if isinstance(_dict[key], str):
                    _res = [_dict[key]]
                elif isinstance(_dict[key], unicode):
                    _res = [_dict[key]]
                elif isinstance(_dict[key], list):
                    _res = _dict[key]
        else:
            _res = []
    except KeyError:
        _res = []
    return _res

def stringify(_dict, scope='general'):
    """Convert `dict` to string, depending on `scope`"""
    _list = []
    if scope == 'general':
        _list += _get_datum(_dict, 'kMDItemTitle')
        _list += _get_datum(_dict, 'net_sourceforge_bibdesk_container')
        _list += _get_datum(_dict, 'kMDItemAuthors')
        _list += _get_datum(_dict, 'net_sourceforge_bibdesk_publicationdate')
    elif scope == 'titles':
        _list += _get_datum(_dict, 'kMDItemTitle')
        _list += _get_datum(_dict, 'net_sourceforge_bibdesk_container')
        _list += _get_datum(_dict, 'net_sourceforge_bibdesk_publicationdate')
    elif scope == 'creators':
        _list += _get_datum(_dict, 'kMDItemAuthors')
        _list += _get_datum(_dict, 'net_sourceforge_bibdesk_publicationdate')
    _list = [unicode(x) for x in _list]
    _str = ' '.join(_list)
    return _str 


################################################
# Read BibDesk `bplist` files
################################################

def read_cachedir():
    """Read BibDesk cache dir into Python array"""
    _data = []
    for bib in os.listdir(BIB_DIR):
        bib_path = os.path.join(BIB_DIR, bib)
        with open(bib_path, 'rb') as _file:
            bib_data = ccl_bplist.load(_file)
            _file.close()
        _data.append(bib_data)
    return _data

def read_cachefile(_bib):
    """Read BibDesk cache file into Python dict"""
    bib_path = os.path.join(BIB_DIR, _bib)
    with open(bib_path, 'rb') as _file:
        bib_data = ccl_bplist.load(_file)
        _file.close()
    return bib_data

def get_bibfiles():
    """Get all referenced `.bib` files"""
    data = read_cachedir()
    bibs = []
    for item in data:
        if not item['net_sourceforge_bibdesk_owningfilepath'] in bibs:
            bibs.append(item['net_sourceforge_bibdesk_owningfilepath'])
    return bibs

def get_groups(group):
    """Helper function to get BibDesk Groups"""
    regex = r"@comment{BibDesk %s Groups{(.*?)}}" % group
    bibs = get_bibfiles()
    data = []
    for _bib in bibs:
        with open(_bib, 'rb') as _file:
            _data = _file.read()
            _file.close()
        try:
            plist = re.search(regex, _data, re.S).group(1)
            data += plistlib.readPlistFromString(plist.strip())
        except AttributeError:
            pass
    return data

def get_group_items(group_name):
    """Get all items for Static Group"""
    groups = get_groups('Static')
    data = read_cachedir()

    _items = []
    for group in groups:
        if group['group name'] == group_name:
            items = group['keys']
            _items = items.split(',')

    group_items = []
    for item in data:
        if item['net_sourceforge_bibdesk_citekey'] in _items:
            group_items.append(item)
    return group_items

def get_group_name(wf):
    """Get name of Group from tmp file"""
    with open(wf.cachefile("group_result.txt"), 'r') as _file:
        group = _file.read().decode('utf-8')
        _file.close()
    return group

def get_keyword_items(keyword_name):
    """Get all items for Keyword"""
    data = read_cachedir()

    keyword_items = []
    for item in data:
        for keyword in item['kMDItemKeywords']:
            if keyword == keyword_name:
                keyword_items.append(item)
    return keyword_items

def get_keyword_name(wf):
    """Get name of Keyword from tmp file"""
    with open(wf.cachefile("keyword_result.txt"), 'r') as _file:
        keyword = _file.read().decode('utf-8')
        _file.close()
    return keyword


################################################
# Helper Functions
################################################

def no_results(query,wf):
    """Return no results"""
    #wf.add_item("Error!", "No results found.", 
    #                icon="icons/n_error.png")
    #wf.send_feedback()
    json_res = []
    ctrl_workflow = {"alfredworkflow" :{
                               "variables" : { 
                               "orig_query" : query, 
                               "action" : "change_scope"}}}
    ctrl_arg = {"subtitle" : "Change search scope",
                "arg": json.dumps(ctrl_workflow)}
    _dict = {
	        "title": "No Results found.",
	        "subtitle": "Press CTRL to change search scope",
            "arg" : query,
            "valid": True,
            "mods": {
                "ctrl" : ctrl_arg,
                },    
        }  
                 
    json_res.append(_dict)            
    json.dump({'items': json_res}, sys.stdout)
    
# _applescriptify_str and set_clipboard are added for debugging only. Not used otherwise.
def _applescriptify_str(text):
    """Replace double quotes in text for Applescript string"""
    text = text.replace('"', '" & quote & "')
    text = text.replace('\\', '\\\\')
    return text
    
def set_clipboard(data):
    """Set clipboard to ``data``""" 
    scpt = """
        set the clipboard to "{0}"
    """.format(_applescriptify_str(data))
    subprocess.call(['osascript', '-e', scpt])
    
#def no_results(wf):
#    xml_res = []
#    for item in xml_res:
#        wf.add_item(**item)
#    wf.send_feedback()
################################################
# Prepare XML Feedback for Alfred
################################################

def get_last_names(_lst):
    """Return list of creator last names"""
    names = [x.split(', ') for x in _lst]
    _res = [n[0] for n in names]
    return _res

def info_format(_item):
    """Format key information for item subtitle"""
    # Format creator string // for all types
    creator_ref = 'xxx.'
    try: 
        creators = _item['kMDItemAuthors']
        lasts = get_last_names(creators)
    except KeyError:
        creators = _item['kMDItemEditors']
        lasts = get_last_names(creators)

    if len(lasts) == 1:
        creator_ref = ''.join(lasts)
    elif len(lasts) == 2:
        creator_ref = ' and '.join(lasts)
    elif len(lasts) > 2:
        creator_ref = ', '.join(lasts[:-1])
        creator_ref += ', and ' + lasts[-1]

    # Clean up any BibTeX cruft
    creator_ref = re.sub(r"{(.*?)}", "\\1", creator_ref)

    if not creator_ref[-1] in ['.', '!', '?']:
        creator_ref += '.'

    # Format date string // for all types
    try:
        _date = _item['net_sourceforge_bibdesk_publicationdate'] 
        date_final = str(_date).split('-')[0] + '.'
    except KeyError:
        date_final = 'xxx.'
    
    # Format title string // for all types
    try:
        _title = _item['kMDItemTitle']
        if not _title[-1] in ['.', '!', '?']:
            title_final = _title + '.'
        else:
            title_final = _title
    except KeyError:
        try:
            _title = _item['kMDItemDisplayName']
        except KeyError:
            title_final = 'xxx.'

    return [creator_ref, date_final, title_final]

def prepare_attachments(_item):
    """Get path to pdf attachments"""
    attachments = []
    for _key, _val in _item.items():
        if _key == 'kMDItemWhereFroms' and _val != []:
            for source in _val:
                if 'pdf' in source or 'epub' in source or 'doc' in source or 'docx' in source:
                    if not 'http' in source:
                        clean_file = urllib.unquote(source)
                        _file = clean_file.replace('file://', '')
                        if os.path.isfile(_file):
                            attachments.append(_file)                              
    return attachments


def prepare_feedback(query, data):
    json_res = []
    ids = []
    
    for item in data:
        if item['net_sourceforge_bibdesk_citekey'] not in ids:
            ids.append(item['net_sourceforge_bibdesk_citekey'])

            attx = prepare_attachments(item)
            # Add below for listing of number of attachments.
            #if attx != []:
            #    _dict.update({
            #        'subtitle': sub + ' Attachments: ' + str(len(attx))
            #        })
            #else:
            #    _dict.update({
            #        'subtitle': sub + ' No Attachments '
            #        })        
            
            
            # If item has an attachment
            # Add below for listing of number of attachments.
            if item['net_sourceforge_bibdesk_pubtype'] == 'article':
                entry_type = 'Article'
                if attx == []: 
                    icon_path = 'icons/n_article.png'
                else:
                    icon_path = 'icons/att_article.png'
            elif item['net_sourceforge_bibdesk_pubtype'] == 'book':
                entry_type = 'Book'
                if attx == []:
                    icon_path = 'icons/n_book.png'
                else:
                    icon_path = 'icons/att_book.png'
            elif item['net_sourceforge_bibdesk_pubtype'] == 'incollection':
                entry_type = 'In Collection'
                if attx == []:
                    icon_path = 'icons/n_chapter.png'
                else:
                    icon_path = 'icons/att_book.png'
            elif item['net_sourceforge_bibdesk_pubtype'] == 'inproceedings':
                entry_type = 'In Proceedings'
                if attx == []:
                    icon_path = 'icons/n_conference.png'
                else:
                    icon_path = 'icons/att_conference.png'
            else:
                entry_type = 'Unknown type'
                if attx == []:
                    icon_path = 'icons/n_written.png'
                else:
                    icon_path = 'icons/att_written.png'
            
            info = info_format(item)
            title = info[-1]
            sub = ' '.join(info[:-1]) + ' (' + entry_type + ')'
            _arg = item['net_sourceforge_bibdesk_citekey']
             
            cmd_workflow = {"alfredworkflow" :{
                            "arg" : _arg,
                            "variables" : {
                            "orig_query" : query,    
                            "action" : "export_cite_command"}}}
            cmd_arg = {"subtitle" : "Export cite command",
                       "arg": json.dumps(cmd_workflow)}
                       
                       
            alt_workflow = {"alfredworkflow" :{
                            "arg" : _arg,
                            "variables" : {
                            "orig_query" : query, 
                            "action" : "search_gui"}}}
            alt_arg = {"subtitle" : "Search GUI",
                       "arg": json.dumps(alt_workflow)} 
                       
            ctrl_workflow = {"alfredworkflow" :{
                            "arg" : _arg,
                            "variables" : {
                            "orig_query" : query, 
                            "action" : "change_scope"}}}
            ctrl_arg = {"subtitle" : "Change search scope",
                       "arg": json.dumps(ctrl_workflow)}   
                       
            shift_workflow = {"alfredworkflow" :{
                            "arg" : _arg,
                            "variables" : {
                            "orig_query" : query,     
                            "action" : "open_attachment"}}}
            shift_arg = {"subtitle" : "Open attachment",
                       "arg": json.dumps(shift_workflow)}                                              
          
            _dict = {
		        "title": title,
		        "subtitle": sub,
                "uid": _arg,
                "valid": True,
                "icon": {"path":icon_path},
		        "arg": _arg,
                "mods": {
                    "cmd" : cmd_arg,
                    "alt" : alt_arg,
                    "ctrl" : ctrl_arg,
                    "shift" : shift_arg,
                    },    
            }           
        json_res.append(_dict)    
    return json_res
################################################
# Filters
################################################

def simple_filter(query, scope, wf):
    """Search through BibDesk items"""
    queries = querify(query)
    data = read_cachedir()
    for query in queries:
        data = wf.filter(query, data, key=lambda x: stringify(x, scope))
    if data != []:
        json_res = prepare_feedback(query, data)  
        #for item in prep_res:
        #    wf.add_item(**item)
        #wf.send_feedback()
        json.dump({'items': json_res}, sys.stdout)
    else:
        no_results(query,wf)

def group_filter(query, wf):
    """Search through BibDesk Groups"""
    queries = querify(query)
    statics = get_groups('Static')
    smarts = get_groups('Smart')
    
    for query in queries:
        st_groups = [x['group name'] 
                for x in statics 
                if query.lower() in x['group name'].lower()]
        sm_groups = [x['group name'] 
                for x in smarts 
                if query.lower() in x['group name'].lower()]
    xml = []
    for static in st_groups:
        _dict = {'title': static, 
                'subtitle': "BibDesk Static Group", 
                'valid': True, 
                'arg': static,
                'icon': 'icons/n_collection.png'}
        xml.append(_dict)
        
    for smart in sm_groups:
        _dict = {'title': smart, 
                'subtitle': "BibDesk Smart Group", 
                'valid': True, 
                'arg': smart,
                'icon': 'icons/n_collection.png'}
        xml.append(_dict)
    
    for item in xml:
        wf.add_item(**item)
    wf.send_feedback()

def keyword_filter(query, wf):
    """Search through items' Keywords"""
    _data = read_cachedir()
    queries = querify(query)
    keywords = [x['kMDItemKeywords']
            for x in _data
            if x['kMDItemKeywords'] != []]
    keywords = [item for sublist in keywords for item in sublist]
    
    for query in queries:
        keywords = [k
                for k in keywords
                if query.lower() in k.lower()]
    xml = []
    for tag in keywords:
        _dict = {'title': tag, 
                'subtitle': "BibDesk Keyword", 
                'valid': True, 
                'arg': tag,
                'icon': 'icons/n_tag.png'}
        xml.append(_dict)

    for item in xml:
        wf.add_item(**item)
    wf.send_feedback()

def in_group_filter(query, wf):
    """Search within chosen group"""
    queries = querify(query)
    group_name = get_group_name(wf)
    group_items = get_group_items(group_name)

    for query in queries:
        group_items = wf.filter(query, group_items, key=lambda x: stringify(x))
    
    if group_items != []:
        prep_res = prepare_feedback(group_items)  
        for item in prep_res:
            wf.add_item(**item)
        wf.send_feedback()
    else:
        no_results(wf)

def in_keyword_filter(query, wf):
    """Search within chosen group"""
    queries = querify(query)
    keyword_name = get_keyword_name(wf)
    keyword_items = get_keyword_items(keyword_name)

    for query in queries:
        keyword_items = wf.filter(query, keyword_items, key=lambda x: stringify(x))
    
    if keyword_items != []:
        prep_res = prepare_feedback(keyword_items)  
        for item in prep_res:
            wf.add_item(**item)
        wf.send_feedback()
    else:
        no_results(wf)


def filter(query, scope, wf):
    """Main API method"""

    if scope in ['general', 'creators', 'titles']:
        simple_filter(query, scope, wf)
    elif scope == 'groups':
        group_filter(query, wf)
    elif scope == 'keywords':
        keyword_filter(query, wf)  
    elif scope == 'in-group':
        in_group_filter(query, wf)
    elif scope == 'in-keyword':
        in_keyword_filter(query, wf)
    #elif scope == 'attachments':
    #'in-keyword'
    #    filters_atts()


################################################
# Main Function
################################################

def main(wf):
    
    queries = wf.args[0] # 'epicur'
    scope = wf.args[1] # 'in-keyword'
    filter(queries, scope, wf)
    
    # LIST = [u'kMDItemWhereFroms', u'kMDItemAuthors', u'kMDItemKeywords']
    # STR = FileAlias
    # UNICODE = [u'net_sourceforge_bibdesk_citekey', u'kMDItemCreator', 
    #           u'kMDItemDisplayName', u'kMDItemTitle', 
    #           u'net_sourceforge_bibdesk_pubtype', u'kMDItemDescription', 
    #           u'net_sourceforge_bibdesk_container', 
    #           u'net_sourceforge_bibdesk_owningfilepath']
    # BOOL = net_sourceforge_bibdesk_itemreadstatus

if __name__ == '__main__':
    
    wf = Workflow()
    sys.exit(wf.run(main))  
