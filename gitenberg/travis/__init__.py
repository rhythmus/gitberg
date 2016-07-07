import glob
import subprocess
import uuid
import os


BUILD_EPUB_SCRIPT = """
#!/bin/sh

function build_epub_from_asciidoc {

	asciidoctor -a toc,idprefix=xx_,version=$1 -b xhtml5 -T ./asciidoctor-htmlbook/htmlbook-autogen/ -d book book.asciidoc -o book.html
	git clone https://github.com/gitenberg-dev/HTMLBook

	# make book.html available to jinja2 environment by putting it into templates
	cp book.html asciidoctor-htmlbook/gitberg-machine/templates/

	/usr/bin/python asciidoctor-htmlbook/gitberg-machine/machine.py -o . -m metadata.yaml book.html
	xsltproc -stringparam external.assets.list " " ./HTMLBook/htmlbook-xsl/epub.xsl book.html
	cp ./HTMLBook/stylesheets/epub/epub.css OEBPS
	if [ -e cover.jpg ]; then cp cover.jpg OEBPS/cover.jpg; fi

	# look for first images directory and one found, copy over to ./OEBPS
	find . -name images -type d | head -n 1 | xargs -I {} mv {} ./OEBPS/
	zip -rX book.epub mimetype
	zip -rX book.epub OEBPS/ META-INF/
	if test -d "OEBPS/images/"; then zip -rX book.epub OEBPS/images/ ;fi
	if [ "$2" != "book" ]; then mv book.epub $2.epub; fi    

} 

build_epub_from_asciidoc $1 $2
"""

def source_book(repo_name):

    """
    return the path of document to use as the source for building epub
    """

    repo_id = repo_name.split("_")[-1]
    repo_htm_path = "{repo_id}-h/{repo_id}-h.htm".format(repo_id=repo_id)

    possible_paths = ["book.asciidoc",
                      repo_htm_path,
                      "{}-0.txt".format(repo_id),
                      "{}-8.txt".format(repo_id),
                      "{}.txt".format(repo_id),
                     ]

    # return the first match

    for path in possible_paths:
        if os.path.exists(path):
            return path

    return None


def build_epub_from_asciidoc (version, epub_title):
	"""
	build for asciidoctor input
	"""

	fname = "{}.sh".format(uuid.uuid4())

	try:
	    f = open(fname, "wb")
	    f.write(BUILD_EPUB_SCRIPT.encode('utf-8'))
	    f.close()
	    os.chmod(fname, 0755)

	    output = subprocess.check_output("./{fname} {version} {epub_title}".format(fname=fname, 
	    	  version=version, epub_title=epub_title), 
	    	  shell=True)
	    print (output)
	except Exception as e:
	    print (e)
	finally:
	    os.remove(fname)

def build_epub(repo_name, version, epub_title):

	source_path = source_book(repo_name)

	if source_path == 'book.asciidoc':
		return build_epub_from_asciidoc (version, epub_title)
	elif source_path.endswith('.htm'):
		# epubmaker --title "Anne of the Island" --author "Montgomery, L. M. (Lucy Maud)" 51-h/51-h.htm
		pass
	else:  # return error
	    # error code?
	    # http://stackoverflow.com/questions/6180185/custom-python-exceptions-with-error-codes-and-error-messages
		raise Exception ('no suitable book found')
	# htm

def repo_name_version ():
	from .. import metadata

	md = metadata.pandata.Pandata("metadata.yaml")

	repo_name = md.metadata.get("_repo")
	version = md.metadata.get("_version")

	return (repo_name, version)
