#!/bin/bash

# abort if no menu given
if [ -z "$1" ]; then
	echo "Error: no menu file path given"
	echo "Usage $0 <path/to/menu.pdf>"
	exit 1
fi

# do the upload
# note: the -n flag tells it to look in your ~/.netrc file for login info
# Your netrc file should have the following in it:
#	machine gtkappasig.com
#	login kappasig
#	password ********
#
curl -n --upload-file "$1" -a ftp://gtkappasig.com/www/resources/menu.pdf
