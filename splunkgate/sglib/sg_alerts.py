# -*- coding: utf-8 -*-

__author__  = "bw"
__version__ = "0.1.0"

import shutil
import time
import re
import os
import os.path
import gzip
import traceback
import glob

class alert_handler:
  """Класс загрузки из файла алертов, поступающих от Splunk"""

  _logger = None
  _config = {}

  def __init__(self, logger, config):
    """
    Инициализация класса
    В config передается dict, содежащий конфигурацию SplunkGate
    В logger передает объект-логгер
    """

    self._logger = logger
    self._config = config


  def __purge_old_snapshot(self, dir):
    self._logger.info('Try delete old snaphot file: %s', dir)
    filelist = glob.glob(dir)
    for filename in filelist:
      os.remove(filename)

    self._logger.info('Delete old snaphot file: %s files', len(filelist))


  def __create_snapshot(self, logName, logType):
    """
    Метод создания снапшотов логов от Splunk
    Путь к лог Splunk берется из конфигурационного файла в секции [Splunk].LogPath
    Путь к снапшоту берется из конфигурационного файла в секции [SplunkGate].WorkPath
    Имя снапшота генерируется из текущего timestamp и возвращается в ответе метода.
    """
    try:
      if logType == 1:
        self.__purge_old_snapshot(self._config['snapshotPath'] + '/win_*.log')
        file1 = self._config['snapshotPath'] + '/win_' + str(int(time.time())) + '.log'
      else:
        self.__purge_old_snapshot(self._config['snapshotPath'] + '/unix_*.log')
        file1 = self._config['snapshotPath'] + '/unix_' + str(int(time.time())) + '.log'

      # Если к конфигурационном файле в [SplunkGate].CreateSnapshot стоит значение 'false', то снапшот не создается.
      if self._config['createSnapshot']:
        self._logger.info('Create Splunk log snapshot: ' + file1)

        shutil.move(logName, file1)
        open(logName, 'a').close()

      else:
        file1 = logName

    except Exception, e:
      self._logger.error('Unsuccess create Splunk log snapshot: '+ str(e))
      raise Exception
    else:
      return file1


  def get_alert(self):
    """
    Прочитать из файла сообщения от Splunk.
    Если readOnlyFirstElement = false, из файла читается только первое сообщение
    """
    alerts = {}
    try:
      win = []
      unix = []

      if self._config['logWin']:
        f = self.__create_snapshot(self._config['logWin'], 1)

        with open (f, "r") as file:
          logs = file.readlines()

        for l in logs:
          win.append(l.replace('\n', '').split(';'))

      if self._config['logUnix']:

        f = self.__create_snapshot(self._config['logUnix'], 2)

        with open (f, "r") as file:
          logs = file.readlines()

        for l in logs:
          unix.append(l.replace('\n', '').split(';'))

      alerts = dict(unix=unix, win=win)
      self._logger.info(''.join(['Read Splunk Windows alerts:', str(len(win)), ', Unix alerts:', str(len(unix))]))

    except Exception, e:
      self._logger.error('Unsuccess read alert from Splunk log: ' + str(e))
      raise Exception

    else:
      response = dict(win=[], unix=[])
      if self._config['readOnlyFirstElement'] == False:
        response = alerts

      else:
        w = []
        u = []
        if len(win) > 0:
          w.append(win[0])
          response['win'] = w

        if len(unix) > 0:
          u.append(unix[0])
          response['unix'] = u

        if self._config['debug'] == 'true':
          print response

      return response


  def parse_win_alert(self, alert):
    """Разбор сообщения от Splunk"""

    ticket = {}
    f = None

    self._logger.info("Parse Windows alert: " + str(alert))

    # Получить имя файла с подробным описание проблемы
    try:
      fcomment = alert[7]
      if os.path.isfile(fcomment):
        # Если файл существует, то распаковать его из GZip и прочитать его
        f = gzip.open(fcomment, 'rb')
        t = f.readlines()
        # Выделить интересующие поля
        ticket['alert'] = alert[3]
        for _t in t:
          if 'EventCode' in _t:
            ticket['eventCode'] = _t.split('=')[1]

          if 'EventType' in _t:
            ticket['eventType'] = _t.split('=')[1]

          if 'Message' in _t:
            ticket['message'] = _t.split('=')[1]

          if 'ComputerName' in _t:
            ticket['computerName'] = _t.split('=')[1].lower().replace('\n', '')

        # Сформировать тело сообщения в Jira
        comment = ''.join(['EventCode=', ticket['eventCode'], ';EventType=', ticket['eventType'], ';ComputerName=', ticket['computerName'], ';Message=', ticket['computerName']])
        comment = comment.replace('\n', ';').replace('\r', '')
        ticket['comment'] = comment

        self._logger.info("Parse ticket: %s", ticket)
        return ticket

      else:
        # Если файл не существует, вернуть ошибку
        raise Exception('File not found', fcomment)

    except Exception, e:
      traceback.print_stack()
      self._logger.error('Unsuccess parse Windows alert from Splunk log: ' + str(e))
      print sys.exc_info()
      raise Exception(e)

    finally:
      if f:
        f.close()


  def parse_unix_alert(self, alert):
    """Разбор сообщения от Splunk"""

    ticket = {}
    f = None

    self._logger.info("Parse Unix alert: " + str(alert))
    try:
      fcomment = alert[7]
      if os.path.isfile(fcomment):
        # Если файл существует, то распаковать его из GZip и прочитать его
        f = gzip.open(fcomment, 'rb')
        t = f.readlines()
        # Выделить интересующие поля
        ticket['alert'] = alert[3]
        ticket['message'] = t[1].split(',')[3].replace('"', '')
        _t = t[2].replace('"', '').split(',')
        ticket['computerName'] = _t[3]
        ticket['eventType'] = _t[1]
        ticket['eventCode'] = _t[4]
        ticket['comment'] = ''.join(['EventCode=', ticket['eventCode'], ';EventType=', ticket['eventType'], ';ComputerName=', ticket['computerName'], ';Message=', ticket['message']])

        return ticket

    except Exception, e:
      traceback.print_stack()
      self._logger.error('Unsuccess parse Unix alert from Splunk log: ' + str(e))
      raise Exception(e)

    finally:
      if f:
        f.close()
