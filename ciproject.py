#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from citool import Citool


def projectQuery(queryString):

    # Elenca tutti i progetti che contengono 'queryString'
    
    jenkins = Citool(proxyset, parsed_args.verbosity)
    jenkins.showProjects(queryString)

    return ''

def projectInfo(projectName):

    # Per 'projectName', recupera info sull'ultima build completata e le ultime 10 build.

    jenkins = Citool(proxyset, parsed_args.verbosity)
    jenkins.showBuildStatus(projectName)

    return ''


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Aiuta a tracciare lo stato CI di un progetto in hosting su apache.org")
    parser.add_argument("-v", "--verbosity", type=int, default=0, choices=[0, 1, 2], help="verbosità dell'output")
    parser.add_argument("-p", "--proxy", default="off", choices=["on", "off"], help="utilizza proxy")
    parser.add_argument("-d", "--dump", metavar="all", action="store", help="Elenca tutti i progetti Apache")
    parser.add_argument("-q", "--query", metavar="project-name", action="store", help="Elenca progetti con questo specifico nome")
    parser.add_argument("-s", "--show", metavar="project-name", action="store", help="Elenca stato build per il progetto specificato")
    parsed_args = parser.parse_args()

    if parsed_args.proxy:
        proxyset = parsed_args.proxy.upper()

    if parsed_args.dump:
        jenkins = Citool(proxyset, parsed_args.verbosity)
        jenkins.query()

    if parsed_args.query:
        projectQuery(parsed_args.query)

    if parsed_args.show:
        projectName = parsed_args.show
        projectInfo(projectName)
