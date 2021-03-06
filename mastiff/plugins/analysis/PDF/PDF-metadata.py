#!/usr/bin/env python
"""
  Copyright 2012-2013 The MASTIFF Project, All Rights Reserved.

  This software, having been partly or wholly developed and/or
  sponsored by KoreLogic, Inc., is hereby released under the terms
  and conditions set forth in the project's "README.LICENSE" file.
  For a list of all contributors and sponsors, please refer to the
  project's "README.CREDITS" file.
"""

__doc__ = """
PDF MetaData Plug-in

Plugin Type: PDF
Purpose:
  Extracts any metadata from a PDF using exiftool (http://www.sno.phy.queensu.ca/~phil/exiftool/)

Output:
   metadata.txt - Contains selected pieces of extracted metadata.

Requirements:
  The exiftool binary is required for this plug-in. The binary can be downloaded
  from http://www.sno.phy.queensu.ca/~phil/exiftool/.

TODO:
  Exiftool will miss some metadata, especially if the Info object is present but
  not specified. Future versions of this plug-in will brute force the metadata,
  but PDF-parsing code needs to be written (or import pdf-parser.py).

Configuration Options:
[PDF Metadata]
exiftool = Path to exiftool program
"""

__version__ = "$Id$"

import subprocess
import logging
import os

import mastiff.plugins.category.pdf as pdf

class PDFMetadata(pdf.PDFCat):
    """PDF Metadata plug-in."""

    def __init__(self):
        """Initialize the plugin."""
        pdf.PDFCat.__init__(self)
        self.page_data.meta['filename'] = 'pdf-metadata'

    def analyze(self, config, filename):
        """
        Obtain the command and options from the config file and call the
        external program.
        """
        # make sure we are activated
        if self.is_activated == False:
            return False
        log = logging.getLogger('Mastiff.Plugins.' + self.name)
        log.info('Starting execution.')

        # get my config options
        plug_opts = config.get_section(self.name)
        if plug_opts is None:
            log.error('Could not get %s options.', self.name)
            return False

        # verify external program exists and we can call it
        if not plug_opts['exiftool'] or \
           not os.path.isfile(plug_opts['exiftool']) or \
           not os.access(plug_opts['exiftool'], os.X_OK):
            log.error('%s is not accessible. Skipping.', plug_opts['exiftool'])
            return False

        # run your external program here
        run = subprocess.Popen([plug_opts['exiftool']] + \
                               [ filename ],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               close_fds=True)
        (output, error) = run.communicate()
        if error is not None and len(error) > 0:
            log.error('Error running program: {}'.format(error))
            return False

        metadata = dict()
        keywords = [ 'Creator', 'Create Date', 'Title', 'Author', 'Producer',
                     'Modify Date', 'Creation Date', 'Mod Date', 'Subject',
                     'Keywords', 'Author', 'Metadata Date', 'Description',
                     'Creator Tool', 'Document ID', 'Instance ID', 'Warning']

        # grab only data we are interested in
        for line in output.split('\n'):
            if line.split(' :')[0].rstrip() in keywords:
                metadata[line.split(':')[0].rstrip()] = line.split(' :')[1].rstrip()

        new_table = self.page_data.addTable(title='PDF Document Metadata')

        if len(metadata) == 0:
            # no data
            log.warn("No PDF metadata detected.")
            new_table.addheader([('Message', str)], printHeader=False)
            new_table.addrow(['No PDF metadata detected.' ])
        else:
            # set up output table
            new_table.addheader([('Data', str), ('Value', str)])
            # sort and add to table
            for key in sorted(metadata.iterkeys()):
                new_table.addrow([key, metadata[key]])

        log.debug ('Successfully ran %s.', self.name)

        return self.page_data
