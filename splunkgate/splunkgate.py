#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import httplib, urllib
import uuid
from datetime import datetime, date, time
import time
import ConfigParser
import gzip
import shutil
import os.path
import logging
import sqlite3


class SplunkLogger:
  logger = None
  configParams = {}

  def __init__(self, config):
    self.configParams = config

    self.logger = logging.getLogger(__name__)
    self.logger.setLevel(logging.INFO)
    handler = logging.FileHandler(self.configParams['splunkgate.logpath'] + '/' + 'splunkgate.log')
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s|%(name)s|%(levelname)s|%(message)s')
    handler.setFormatter(formatter)
    self.logger.addHandler(handler)

  def getLogger(self):
    return self.logger


class SplunkAlerts:
  logger = None
  configParams = {}

  def __init__(self, logger, config):
    self.logger = logger
    self.configParams = config

  def createSnapshot(self):
    try:
      file = configParams['splunk.logpath']
      file1 = configParams['splunkgate.workpath'] + str(int(time.time())) + '.log'

      if configParams['splunkgate.isSnapshot']:
        logger.info('Create Splunk log snapshot: ' + file1)

        shutil.move(file, file1)
        open(file, 'a').close()
      
      else:
        file1 = file

    except Exception, e:
      self.logger.error('Unsuccess create Splunk log snapshot: '+ str(e))
      raise Exception
    else:
      return file1

  def getAlert(self, isOnlyFirstElement = False):
    alerts = []
    try:
      f = self.createSnapshot()

      with open (f, "r") as file:
        logs = file.readlines()

      for l in logs:
        alerts.append(l.replace('\n', '').split(';'))

      logger.info('Read Splunk alerts: ' + str(len(alerts)))

    except Exception, e:
      self.logger.error('Unsuccess read alert from Splunk log: '+ str(e))
      raise Exception

    else:
      response = []
      if isOnlyFirstElement == False:
        response = alerts
      
      else:
        a = []
        if len(alerts) > 0:
          a.append(alerts[0])
          response = a
        else:
          pass
        if self.configParams['splunk.debug'] == 'true':
          print response

      return response

class SplunkConfig:
  configParams = {}

  def __init__(self, configFile):
    try:
      cfg = ConfigParser.ConfigParser()
      cfg.read(configFile)
      self.configParams['esb.routeId'] = cfg.get('ESB', 'RouteID', '')
      self.configParams['esb.serviceId'] = cfg.get('ESB', 'ServiceID', '')
      self.configParams['esb.login'] = cfg.get('ESB', 'Login', '')
      self.configParams['esb.password'] = cfg.get('ESB', 'Password', '')
      self.configParams['esb.host'] = cfg.get('ESB', 'Host', '')
      self.configParams['esb.url'] = cfg.get('ESB', 'URL', '')
      self.configParams['splunk.logpath'] = cfg.get('Splunk', 'LogPath', '')
      self.configParams['splunk.debug'] = cfg.get('Splunk', 'debugAlerts', '')
      self.configParams['splunkgate.logpath'] = cfg.get('SplunkGate', 'LogPath', '')
      self.configParams['splunkgate.workpath'] = cfg.get('SplunkGate', 'WorkPath', '')
      isSnapshot = cfg.get('SplunkGate', 'isSnapshot', '')
      if 'no' in isSnapshot:
        self.configParams['splunkgate.isSnapshot'] = False
      else:
        self.configParams['splunkgate.isSnapshot'] = True
      self.configParams['splunkgate.db'] = cfg.get('SplunkGate', 'Database', '')
      
      servers = cfg.get('Splunk', 'Servers', '').split('\n')
      serverProject = {}
      for server in servers:
        s = server.split(':')
        serverProject[s[0].strip()] = s[1].strip()
        self.configParams['splunk.servers'] = serverProject

    except Exception, e:
      print 'Unsuccess get SplunkGate configuration: ' + str(e)

  def getConfigParams(self):
    return self.configParams


class SplunkDB:
  logger = None
  configParams = {}
  conn = None

  def __init__(self, logger, config):
    cur = None
    self.logger = logger
    self.configParams = config
    self.conn = sqlite3.connect(configParams['splunkgate.db'])
    self.conn.text_factory = str

    with self.conn:
      cur = self.conn.cursor()
      cur.execute('create table if not exists tickets (event_code integer, event_type integer, computer_name varchar(1000), message varchar(2048), message_id varchar(1024), create_date timestamp not null default current_timestamp, send_to_esb_date timestamp, esb_status varchar(1024), primary key(event_code, event_type, computer_name))')
      cur.close()
      self.conn.commit()

  def setTicket(self, eventCode, eventType, computerName, message, messageId):
    with self.conn:
      cur = self.conn.cursor()
      cur.execute('insert into tickets (event_code, event_type, computer_name, message, message_id) values (?, ?, ?, ?, ?)', (eventCode, eventType, computerName, message, str(messageId)))
      self.conn.commit()
      cur.close()


  def getTicket(self, eventCode, eventType, computerName):
    ticket = {}
    with self.conn:
      cur = self.conn.cursor()
      cur.execute('select event_code, event_type, computer_name, message, message_id from tickets where event_code = ? and event_type = ? and computer_name = ?', (eventCode, eventType, computerName))
      row = cur.fetchone()
      if row:
        ticket['eventCode'] = row[0]
        ticket['eventType'] = row[1]
        ticket['computerName'] = row[2]
        ticket['message'] = row[3]
        ticket['messageId'] = row[4]

      cur.close()
      return ticket

  def updateTicket(self, status, eventCode, eventType, computerName):
    with self.conn:
      cur = self.conn.cursor()
      cur.execute('update tickets set send_to_esb_date = current_timestamp, esb_status = ? where event_code = ? and event_type = ? and computer_name = ?', (status, eventCode, eventType, computerName))
      self.conn.commit()


class SplunkGate:
  logger = None
  configParams = {}

  def __init__(self, logger, config):
    self.logger = logger
    self.configParams = config

  def createSOAPMessage(self, id, systemCode, task, comment, priority):
    param = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:typ="http://ish.curs.kz/SyncChannel/v10/Types">
      <soapenv:Header/>
      <soapenv:Body>
        <typ:SendMessage>
          <request>
            <requestInfo>
              <messageId>""" + str(id) + """</messageId>
              <serviceId>""" + self.configParams["esb.serviceId"] + """</serviceId>
              <messageDate>""" + str(datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%s%z")) + """</messageDate>
              <routeId>""" + self.configParams["esb.routeId"] + """</routeId>
              <sender>
                <senderId>""" + self.configParams["esb.login"] + """</senderId>
                <password>""" + self.configParams["esb.password"] +"""</password>
              </sender>
              <properties>
                <key/>
                <value/>
              </properties>
              <sessionId/>
            </requestInfo>
            <requestData>
              <data>
                <Systems>
                  <Systemcode>""" + systemCode + """</Systemcode>
                  <Task>""" + task + """</Task>
                  <Comment>""" + comment + """</Comment>
                  <Priority>""" + priority + """</Priority>
                </Systems>
              </data>
            </requestData>
          </request>
        </typ:SendMessage>
      </soapenv:Body>
    </soapenv:Envelope>"""

    return param

  def sendSOAPMessage(self, message):
    data = None

    headers = {"Content-type": "text/xml; charset=utf-8", "SOAPAction": ""}

    log = ''.join(['Call ESB: host=http://', self.configParams['esb.host'], self.configParams['esb.url'], ';http headers=', str(headers), ';message=', message])
    self.logger.info(log)

    try:
      conn = httplib.HTTPConnection(self.configParams["esb.host"])
      conn.request("POST", self.configParams["esb.url"], message, headers)
      response = conn.getresponse()
      status = response.status
      reason = response.reason

      log = ''.join(['Success call ESB: status=', str(status), ';reason=', str(reason), ';data=', str(response.read())])
      self.logger.info(log)

      data = response.read()

    except Exception, e:
      self.logger.error('Unsuccess call ESB: '+ str(e))

    finally:
      conn.close()

    return data


if __name__ == "__main__":
  config = SplunkConfig(sys.argv[1])
  configParams = config.getConfigParams()

  splunkLogger = SplunkLogger(configParams)
  logger = splunkLogger.getLogger()

  logger.info('Start SplunkGate')

  splunkAlerts = SplunkAlerts(logger, configParams)
  alerts = splunkAlerts.getAlert(True)

  db = SplunkDB(logger, configParams)

  #gate = SplunkGate(logger, configParams)

  for alert in alerts:
    eventCode = None
    eventType = None
    message = None
    computerName = None

    #print alert
    fcomment = alert[7]
    if os.path.isfile(fcomment):
      f = gzip.open(fcomment, 'rb')
      t = f.readlines()
      eventCode = t[4][0:-1].split('=')[1]
      eventType = t[5][0:-1].split('=')[1]
      message = t[12][0:-1].split('=')[1]   
      computerName = t[7][0:-1].split('=')[1]
      f.close()
      comment = t[4] + t[5] + t[7] + t[12]
    else:
      comment = ''

    id = uuid.uuid1()

    logger.info(str(alert) + '\n' + comment)
    print id, eventCode, eventType, computerName, message

    print configParams['splunk.servers'].get(computerName)

    ticket = None
    ticket = db.getTicket(eventCode, eventType, computerName)
    if not ticket:
      db.setTicket(eventCode, eventType, computerName, message, id)

      #message = gate.createSOAPMessage(id, 'SMAC', alert[3], comment, 'P002')
      #response = gate.sendSOAPMessage(message)
      #logger.info(''.join(['Get response: ', str(response)]))
      db.updateTicket(status, eventCode, eventType, computerName)

  logger.info('Stop SplunkGate')
