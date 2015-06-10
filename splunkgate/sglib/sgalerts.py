# -*- coding: utf-8 -*-

import time
import os.path
import gzip

class AlertHandler:
  """Класс загрузки из файла алертов, поступающих от Splunk"""

  logger = None
  config = {}

  def __init__(self, logger, config):
    """
    Инициализация класса
    В config передается dict, содежащий конфигурацию SplunkGate
    В logger передает объект-логгер
    """

    self.logger = logger
    self.config = config


  def createSnapshot(self):
    """
    Метод создания снапшотов логов от Splunk
    Путь к лог Splunk берется из конфигурационного файла в секции [Splunk].LogPath
    Путь к снапшоту берется из конфигурационного файла в секции [SplunkGate].WorkPath
    Имя снапшота генерируется из текущего timestamp и возвращается в ответе метода.
    """
    try:
      file = self.config['log']
      file1 = self.config['snapshotPath'] + str(int(time.time())) + '.log'

      # Если к конфигурационном файле в [SplunkGate].CreateSnapshot стоит значение 'false', то снапшот не создается.
      if self.config['createSnapshot']:
        self.logger.info('Create Splunk log snapshot: ' + file1)

        shutil.move(file, file1)
        open(file, 'a').close()

      else:
        file1 = file

    except Exception, e:
      self.logger.error('Unsuccess create Splunk log snapshot: '+ str(e))
      raise Exception
    else:
      return file1


  def getAlert(self):
    """
    Прочитать из файла сообщения от Splunk.
    Если readOnlyFirstElement = false, из файла читается только первое сообщение
    """
    alerts = []
    try:
      f = self.createSnapshot()

      with open (f, "r") as file:
        logs = file.readlines()

      for l in logs:
        alerts.append(l.replace('\n', '').split(';'))

      self.logger.info('Read Splunk alerts: ' + str(len(alerts)))

    except Exception, e:
      self.logger.error('Unsuccess read alert from Splunk log: ' + str(e))
      raise Exception

    else:
      response = []
      if self.config['readOnlyFirstElement'] == False:
        response = alerts

      else:
        a = []
        if len(alerts) > 0:
          a.append(alerts[0])
          response = a
        else:
          pass
        if self.config['debug'] == 'true':
          print response

      return response


  def parseAlert(self, alert):
    """Разбор сообщения от Splunk"""

    ticket = {}
    f = None

    self.logger.info("Parse alert: " + str(alert))

    # Получить имя файла с подробным описание проблемы
    try:
      fcomment = alert[7]
      if os.path.isfile(fcomment):
        # Если файл существует, то распаковать его из GZip и прочитать его
        f = gzip.open(fcomment, 'rb')
        t = f.readlines()

        # Выделить интересующие поля
        ticket['alert'] = alert[3]
        ticket['eventCode'] = t[4][0:-1].split('=')[1]
        ticket['eventType'] = t[5][0:-1].split('=')[1]
        ticket['message'] = t[12][0:-1].split('=')[1]
        ticket['computerName'] = t[7][0:-1].split('=')[1]

        # Сформировать тело сообщения в Jira
        comment = t[4] + t[5] + t[7] + t[12]
        comment = comment.replace('\n', ';').replace('\r', '')
        ticket['comment'] = comment

        self.logger.info("Parse ticket: " + str(ticket))
        return ticket

      else:
        # Если файл не существует, вернуть ошибку
        raise Exception('File not found', fcomment)

    except Exception, e:
      self.logger.error('Unsuccess parse alert from Splunk log: ' + str(e))
      raise Exception(e)

    finally:
      if f:
        f.close()
