#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import re
import sys
import collections
import logging
import time


class Citool(object):

    # Classe base di Jenkins che implementa la ricerca

    def __init__(self, proxyset, verbosity):

        """ Parti di URL che devono essere utilizzate dai vari metodi

        Se è definito il proxy, cambia la URL del proxy per utilizzare quella definita.
        Funziona con Python v2.7.x, non testato in v3.x
        """

        self.pyapi     = 'api/python?pretty=true'
        self.buildurl  = 'https://builds.apache.org/'
        self.proxyset  = proxyset
        self.verbosity = verbosity

        if self.proxyset == "ON":
            # configurazione proxy per urllib2
            proxy = urllib2.ProxyHandler({'https' : 'proxy-url-domain-name.com:port_number'})
            opener = urllib2.build_opener(proxy)
            urllib2.install_opener(opener)

        if self.verbosity == 0:
            logLevel = logging.INFO
        if self.verbosity == 1:
            logLevel = logging.WARNING
        if self.verbosity == 2:
            logLevel = logging.DEBUG

        logFormat = "{{ %(asctime)s  == %(levelname)-8s  ==Module:%(module)s  Function:%(funcName)s Line:%(lineno)d }} %(message)s "
        logging.basicConfig(level=logLevel, format=logFormat, datefmt='%m/%d/%Y %I:%M:%S %p')


    def query(self, *thisProject):

        """ Se 'thisProject' è vuoto, elenca tutti i nomi di progetto in Tcloud Jenkins

        Se 'thisProject' non è valido, esci con un messaggio.
        Se 'thisProject' è valido, ritorna l'URL tcloud di Jenkins del progetto.
        """

        allProjects = eval(urllib2.urlopen(self.buildurl + self.pyapi).read())

        if len(thisProject) == 0:
            logging.info("Elenco i nomi di progetti in hosting su builds.apache.org")
            for project in allProjects['jobs']:
                print project.get('name')
            return ''
        elif thisProject[0]:
            logging.info("Controllo %s in elenco progetti..." %(thisProject[0]))
            for i in allProjects['jobs']:
                if thisProject[0] == i['name']:
                    logging.info("Corrispondenza {0} con {1}".format(thisProject[0], i['name']))
                    logging.info("L'URL del progetto per avere più info è {}".format(i['url']))
                    return i['url']
            else:
                logging.warning("Progetto non valido, %s, esco." %(thisProject[0]))
                sys.exit()


    def getBuildTime(self, buildInfo):

        # Ritorna gli orari di inizio e completamento dalla struttura 'buildInfo'.

        self.buildInfo = buildInfo

        unixtime = self.buildInfo['timestamp']
        duration = self.buildInfo['duration']

        startTime = time.strftime('%a %b %d %H:%M:%S', time.gmtime(unixtime/1000))
        runTime   = time.strftime('%H:%M:%S', time.gmtime(duration/1000))

        return (startTime, runTime)

    def getBuildCause(self, buildInfo):

        # Dalla struttura dati 'buildInfo', ritorna l'evento che ha scatenato la build.

        self.buildInfo = buildInfo

        for i in buildInfo['actions']:
            if i.has_key('causes'):
                causeInfo = i['causes']
                break

        for j in causeInfo:
            if j.has_key('shortDescription'):
                buildCause = j['shortDescription']
                break

        buildCause = re.sub("Iniziato da ", "", buildCause)

        return buildCause


    def showLatestBuild(self, projectInfo):

        """ Usando 'projectInfo' (output API REST), ottieni:

        URL dell'ultima build completata e dell'evento che la ha scatenata.
        """

        logging.info("L'ultima build completata di {0} è {1}".format(self.projectName, projectInfo['lastCompletedBuild']['url']))
        lastBuildInfo = eval(urllib2.urlopen(projectInfo['lastCompletedBuild']['url'] + self.pyapi).read())

        buildStartedAt, buildEndedAt = self.getBuildTime(lastBuildInfo)
        startedBy = self.getBuildCause(lastBuildInfo)
        if lastBuildInfo['building'] == False and lastBuildInfo['result'] == "SUCCESS":
            print("La build è stata iniziata da {0}".format(startedBy))
            print("Ed è stata completata senza errori")
        if lastBuildInfo['building'] == False and lastBuildInfo['result'] == "FAILURE":
            print("La build è stata iniziata da {0}".format(startedBy))
            print("E non è stata completata a causa di errori")
        if lastBuildInfo['building'] == False and lastBuildInfo['result'] == "ABORTED":
            print("La build è stata iniziata da {0}".format(startedBy))
            print("Ed è stata abortita")

        return ''



    def showLastTen(self, projectInfo):

        """ Usando 'projectInfo' (output API REST), ottieni:

        breve statistica sullo stato di completamento delle ultime 10 build di questo progetto.
        """

        counter = 1
        buildStats = collections.OrderedDict()
        buildUrls = []
        buildResult = []

        allBuilds = projectInfo['builds']

        for b in allBuilds:
            if counter <= 10:
                thisBuildInfo = eval(urllib2.urlopen(b['url'] + self.pyapi).read())
                buildUrls.append(b['url'])
                if thisBuildInfo['building'] == True:
                    buildResult.append("Build in corso")
                else:
                    buildResult.append(thisBuildInfo['result'])
            counter += 1

        for job, status in zip(buildUrls, buildResult):
            print("Stato della build, {0}: {1}".format(job, status))
            buildStats.update({job : status})

        return ''

    def showProjects(self, projectString):

        """ Per 'projectName', interroga il tcloud jenkins ed elenca

        i nomi dei progetti che contengono 'projectString'.
        """

        projects = []
        matched  = []

        self.projectString = projectString

        logging.debug("Python API per strumento CI: %s" %(self.buildurl + self.pyapi))
        allProjects = eval(urllib2.urlopen(self.buildurl + self.pyapi).read())

        logging.info("Recupero nomi di tutti i progetti...")
        for i in allProjects['jobs']:
            projects.append(i['name'])
        logging.info("Controllo %s in elenco progetti..." %(self. projectString))
        lookupStr = re.compile(self.projectString, re.IGNORECASE)
        for i in projects:
            lookupResult = re.findall(lookupStr, i)
            logging.debug("Risultati ricerca: %s" %(lookupResult))
            if len(lookupResult) != 0:
                matched.append(i)

        for prj in matched:
            print("Il progetto {0} corrisponde alla stringa di ricerca".format(prj))

        return ''


    def showBuildStatus(self, projectName):

        """ Per 'projectName', interroga il tcloud jenkins ed estrae i dettagli

        dello stato dell'ultima build completata e brevi statistiche sulle ultime
        10 build completate.
        """

        self.projectName = projectName
        projectUrl = self.query(self.projectName)

        newBuildurl = projectUrl + "/" + self.pyapi
        projectInfo = eval(urllib2.urlopen(newBuildurl).read())

        self.showLatestBuild(projectInfo)
        self.showLastTen(projectInfo)

        return ''
