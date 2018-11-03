# -*- coding: utf-8 -*-
# Copyright (C) 2011 by Peter Goodman
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import urllib2
import urlparse
from BeautifulSoup import *
from collections import defaultdict
import re
import sqlite3 as lite
from sqlite3 import Error
def attr(elem, attr):
    """An html attribute from an html element. E.g. <a href="">, then
    attr(elem, "href") will get the href or an empty string."""
    try:
        return elem[attr]
    except:
        return ""

WORD_SEPARATORS = re.compile(r'\s|\n|\r|\t|[^a-zA-Z0-9\-_]')

class crawler(object):
    """Represents 'Googlebot'. Populates a database by crawling and indexing
    a subset of the Internet.

    This crawler keeps track of font sizes and makes it simpler to manage word
    ids and document ids."""

    docIndex = list() #doc URL indexed by id
    lexicon = list() #words indexed by id
    invertedIndex = dict() #lists of doc ids indexed by word id

    wordsInDocs = dict() #lists of words indexed by doc id
    urlLinks = list() #list of ordered pairs (tuples) in the form ('from' docId, 'to' docId)
    pageRanks = dict() #page rank indexed by document id

    def __init__(self, db_conn, url_file):
        """Initialize the crawler with a connection to the database to populate
        and with the file containing the list of seed URLs to begin indexing."""
        self._url_queue = [ ]
        self._doc_id_cache = { }
        self._word_id_cache = { }

        # functions to call when entering and exiting specific tags
        self._enter = defaultdict(lambda *a, **ka: self._visit_ignore)
        self._exit = defaultdict(lambda *a, **ka: self._visit_ignore)

        # add a link to our graph, and indexing info to the related page
        self._enter['a'] = self._visit_a

        # record the currently indexed document's title an increase
        # the font size
        def visit_title(*args, **kargs):
            self._visit_title(*args, **kargs)
            self._increase_font_factor(7)(*args, **kargs)

        # increase the font size when we enter these tags
        self._enter['b'] = self._increase_font_factor(2)
        self._enter['strong'] = self._increase_font_factor(2)
        self._enter['i'] = self._increase_font_factor(1)
        self._enter['em'] = self._increase_font_factor(1)
        self._enter['h1'] = self._increase_font_factor(7)
        self._enter['h2'] = self._increase_font_factor(6)
        self._enter['h3'] = self._increase_font_factor(5)
        self._enter['h4'] = self._increase_font_factor(4)
        self._enter['h5'] = self._increase_font_factor(3)
        self._enter['title'] = visit_title

        # decrease the font size when we exit these tags
        self._exit['b'] = self._increase_font_factor(-2)
        self._exit['strong'] = self._increase_font_factor(-2)
        self._exit['i'] = self._increase_font_factor(-1)
        self._exit['em'] = self._increase_font_factor(-1)
        self._exit['h1'] = self._increase_font_factor(-7)
        self._exit['h2'] = self._increase_font_factor(-6)
        self._exit['h3'] = self._increase_font_factor(-5)
        self._exit['h4'] = self._increase_font_factor(-4)
        self._exit['h5'] = self._increase_font_factor(-3)
        self._exit['title'] = self._increase_font_factor(-7)

        # never go in and parse these tags
        self._ignored_tags = set([
            'meta', 'script', 'link', 'meta', 'embed', 'iframe', 'frame', 
            'noscript', 'object', 'svg', 'canvas', 'applet', 'frameset', 
            'textarea', 'style', 'area', 'map', 'base', 'basefont', 'param',
        ])

        # set of words to ignore
        self._ignored_words = set([
            '', 'the', 'of', 'at', 'on', 'in', 'is', 'it',
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
            'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
            'u', 'v', 'w', 'x', 'y', 'z', 'and', 'or',
        ])

        # TODO remove me in real version
        self._mock_next_doc_id = 0
        self._mock_next_word_id = 0

        # keep track of some info about the page we are currently parsing
        self._curr_depth = 0
        self._curr_url = ""
        self._curr_doc_id = 0
        self._font_size = 0
        self._curr_words = None

        # get all urls into the queue
        try:
            with open(url_file, 'r') as f:
                for line in f:
                    self._url_queue.append((self._fix_url(line.strip(), ""), 0))
        except IOError:
            pass
    
    # TODO remove me in real version
    def _mock_insert_document(self, url):
        """A function that pretends to insert a url into a document db table
        and then returns that newly inserted document's id."""
        ret_id = self._mock_next_doc_id
        self._mock_next_doc_id += 1
        return ret_id
    
    # TODO remove me in real version
    def _mock_insert_word(self, word):
        """A function that pretends to inster a word into the lexicon db table
        and then returns that newly inserted word's id."""
        ret_id = self._mock_next_word_id
        self._mock_next_word_id += 1
        return ret_id
    
    def word_id(self, word):
        """Get the word id of some specific word."""
        
        #add the word to wordsInDocs for the current document
        self.wordsInDocs[self._curr_doc_id].append(word)

        if word in self._word_id_cache:
            return self._word_id_cache[word]
        
        # TODO: 1) add the word to the lexicon, if that fails, then the
        #          word is in the lexicon
        #       2) query the lexicon for the id assigned to this word, 
        #          store it in the word id cache, and return the id.

	#add the word to the lexicon if it's not already there
        word_id = self._mock_insert_word(word)
		
        if word not in self.lexicon:
	        self.lexicon.insert(word_id, word)
	
	#add word id to cache
        self._word_id_cache[word] = word_id
        return word_id
    
    def document_id(self, url):
        """Get the document id for some url."""
        if url in self._doc_id_cache:
            return self._doc_id_cache[url]
        
        # TODO: just like word id cache, but for documents. if the document
        #       doesn't exist in the db then only insert the url and leave
        #       the rest to their defaults.
        
	#add the doc to the lexicon if it's not already there
        doc_id = self._mock_insert_document(url)

        if url not in self.docIndex:
	        self.docIndex.insert(doc_id, url)

        #create empty list of words in this document in wordsInDocs
        self.wordsInDocs[doc_id] = list()

	#add doc to cache
        self._doc_id_cache[url] = doc_id
        return doc_id
    
    def _fix_url(self, curr_url, rel):
        """Given a url and either something relative to that url or another url,
        get a properly parsed url."""

        rel_l = rel.lower()
        if rel_l.startswith("http://") or rel_l.startswith("https://"):
            curr_url, rel = rel, ""
            
        # compute the new url based on import 
        curr_url = urlparse.urldefrag(curr_url)[0]
        parsed_url = urlparse.urlparse(curr_url)
        return urlparse.urljoin(parsed_url.geturl(), rel)

    def add_link(self, from_doc_id, to_doc_id):
        """Add a link into the database, or increase the number of links between
        two pages in the database."""
        # TODO

    def _visit_title(self, elem):
        """Called when visiting the <title> tag."""
        title_text = self._text_of(elem).strip()
        print "document title="+ repr(title_text)

        # TODO update document title for document id self._curr_doc_id
    
    def _visit_a(self, elem):
        """Called when visiting <a> tags."""

        dest_url = self._fix_url(self._curr_url, attr(elem,"href"))

        #print "href="+repr(dest_url), \
        #      "title="+repr(attr(elem,"title")), \
        #      "alt="+repr(attr(elem,"alt")), \
        #      "text="+repr(self._text_of(elem))

        # add the just found URL to the url queue
        self._url_queue.append((dest_url, self._curr_depth))
        
        # add a link entry into the database from the current document to the
        # other document
        self.add_link(self._curr_doc_id, self.document_id(dest_url))

        #add ordered pair (curr id, dest id) to the url graph
        self.urlLinks.append((self._curr_doc_id, self.document_id(dest_url)))

        # TODO add title/alt/text to index for destination url
    
    def _add_words_to_document(self):
        # TODO: knowing self._curr_doc_id and the list of all words and their
        #       font sizes (in self._curr_words), add all the words into the
        #       database for this document

	    print "    num words="+ str(len(self._curr_words))

    def _increase_font_factor(self, factor):
        """Increade/decrease the current font size."""
        def increase_it(elem):
            self._font_size += factor
        return increase_it
    
    def _visit_ignore(self, elem):
        """Ignore visiting this type of tag"""
        pass

    def _add_text(self, elem):
        """Add some text to the document. This records word ids and word font sizes
        into the self._curr_words list for later processing."""
        words = WORD_SEPARATORS.split(elem.string.lower())
        for word in words:
            word = word.strip()
            if word in self._ignored_words:
                continue
            self._curr_words.append((self.word_id(word), self._font_size))
        
    def _text_of(self, elem):
        """Get the text inside some element without any tags."""
        if isinstance(elem, Tag):
            text = [ ]
            for sub_elem in elem:
                text.append(self._text_of(sub_elem))
            
            return " ".join(text)
        else:
            return elem.string

    def _index_document(self, soup):
        """Traverse the document in depth-first order and call functions when entering
        and leaving tags. When we come accross some text, add it into the index. This
        handles ignoring tags that we have no business looking at."""
        class DummyTag(object):
            next = False
            name = ''
        
        class NextTag(object):
            def __init__(self, obj):
                self.next = obj
        
        tag = soup.html
        stack = [DummyTag(), soup.html]

        while tag and tag.next:
            tag = tag.next

            # html tag
            if isinstance(tag, Tag):

                if tag.parent != stack[-1]:
                    self._exit[stack[-1].name.lower()](stack[-1])
                    stack.pop()

                tag_name = tag.name.lower()

                # ignore this tag and everything in it
                if tag_name in self._ignored_tags:
                    if tag.nextSibling:
                        tag = NextTag(tag.nextSibling)
                    else:
                        self._exit[stack[-1].name.lower()](stack[-1])
                        stack.pop()
                        tag = NextTag(tag.parent.nextSibling)
                    
                    continue
                
                # enter the tag
                self._enter[tag_name](tag)
                stack.append(tag)

            # text (text, cdata, comments, etc.)
            else:
                self._add_text(tag)

    '''#populate the urlGraph structure and calculate all pageranks
    def get_page_ranks(self, docID, depth):
        #Step 1: Populate urlGraph structure

        #find <a> tag on the current page
        #follow it
        #repeat this recursively, decreasing the depth with each call. when the depth is 0, return
        #if any of the webpages listed in urls.txt are encountered, add them to all applicable docId's entries in urlGraph
        #e.g.: if A->B->C, then C needs to be added to B with a depth of 1, and C needs to be added to A with a depth of 2

        #Step 2: Calculate page rank
        #For each key in urlGraph, count number of times each docID appears'''

    
    def page_rank(self, links, num_iterations=20, initial_pr=1.0):
        from collections import defaultdict
        import numpy as np

        page_rank = defaultdict(lambda: float(initial_pr))
        num_outgoing_links = defaultdict(float)
        incoming_link_sets = defaultdict(set)
        incoming_links = defaultdict(lambda: np.array([]))
        damping_factor = 0.85

        # collect the number of outbound links and the set of all incoming documents
        # for every document

        for (from_id,to_id) in links:
            num_outgoing_links[int(from_id)] += 1.0
            incoming_link_sets[to_id].add(int(from_id))
    
        # convert each set of incoming links into a numpy array
        for doc_id in incoming_link_sets:
            incoming_links[doc_id] = np.array([from_doc_id for from_doc_id in incoming_link_sets[doc_id]])

        num_documents = float(len(num_outgoing_links))
        lead = (1.0 - damping_factor) / num_documents
        partial_PR = np.vectorize(lambda doc_id: page_rank[doc_id] / 1 if num_outgoing_links[doc_id] == 0 else (num_outgoing_links[doc_id]))

        for _ in xrange(num_iterations):
            for doc_id in num_outgoing_links:
                tail = 0.0
                if len(incoming_links[doc_id]):
                    tail = damping_factor * partial_PR(incoming_links[doc_id]).sum()
                page_rank[doc_id] = lead + tail
    
        return page_rank

    def get_inverted_index(self):
	invIndex = dict()

	for w in self._word_id_cache:
            #check if word id has been used as indexed yet, if not, create a new set of docs associated with it
            if self.lexicon.index(w) not in invIndex.keys(): 
                invIndex[self.lexicon.index(w)] = set()
	    for d in self.wordsInDocs:
		if w in self.wordsInDocs[d]: #if a given word id is associated with a given doc id
		    invIndex[self.lexicon.index(w)].add(d) #add the doc id to the set

	self.invertedIndex = invIndex
	return invIndex

    def get_resolved_inverted_index(self):
        invIndex = dict()
        res_invIndex = dict()
        self.get_inverted_index()
        invIndex=self.invertedIndex
        #for key, value in invIndex.items():
            #print key, value
        for key,value in invIndex.items():
          res_invIndex[self.lexicon[key]]=set()
          x=self.lexicon[key]
          for m in value:
               res_invIndex[x].add(self.docIndex[m])
        
        return res_invIndex 

    def add_to_database(self):
        curr=lite.connect("C:\\sqlite\db5\pythonsqlite.db")  
        cur=curr.cursor()  

        #create table with document information (id, url, words, pagerank)
        cur.execute("CREATE TABLE DocInfo (doc_id integer, url text, words text,pgrank real)")

        for x in range(len(self.docIndex)):
            newwords=' '.join(self.wordsInDocs[x])
            cur.execute("INSERT INTO DocInfo VALUES('" + str(x) + "','" + self.docIndex[x] + "','" + newwords + "','" + str(self.pageRanks[x]) + "')")
        
        #create table with word information (id, word, documents)
        cur.execute("CREATE TABLE WordInfo (word_id integer, word text, doc_containing_word text)")

        for x in range(len(self.lexicon)):
            docs = ' '.join(str(i) for i in self.invertedIndex[x])
            cur.execute("INSERT INTO WordInfo VALUES('" + str(x) + "','" + self.lexicon[x] + "','" + docs + "')")
        
        curr.commit()
        curr.close()

    def crawl(self, depth=0, timeout=3):
        """Crawl the web!"""
        seen = set()
	
        print(self._url_queue)

        while len(self._url_queue):
            url, depth_ = self._url_queue.pop()

            # skip this url; it's too deep
            if depth_ > depth:
                continue

            doc_id = self.document_id(url)

            # we've already seen this document
            if doc_id in seen:
                continue

            seen.add(doc_id) # mark this document as hasn't been visited
            
            socket = None
            try:
                socket = urllib2.urlopen(url, timeout=timeout)
                soup = BeautifulSoup(socket.read())

                self._curr_depth = depth_ + 1
                self._curr_url = url
                self._curr_doc_id = doc_id
                self._font_size = 0
                self._curr_words = [ ]
                self._index_document(soup)
                self._add_words_to_document()
                print "    url="+repr(self._curr_url)

            except Exception as e:
                print e
                pass
            finally:
                if socket:
                    socket.close()
        
        #calculate page ranks
        self.pageRanks = self.page_rank(self.urlLinks)

        for i in range(len(self.docIndex)):
            if i not in self.pageRanks.keys():
                self.pageRanks[i] = 0

        #create inverted index
        self.get_inverted_index()

        print self.urlLinks
        print self.pageRanks

        self.add_to_database()

        #for testing purposes
        #print(self.docIndex)
        #print(self.lexicon)
        #print(self.wordsInDocs)
        
        #for key, value in self.invertedIndex.iteritems():
            #print key, value
        
        #res=self.get_resolved_inverted_index()
        #for key, value in res.items():
           #print key, value

if __name__ == "__main__":
    bot = crawler(None, "urls.txt")
    bot.crawl(depth=0)


