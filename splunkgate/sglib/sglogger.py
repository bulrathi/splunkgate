# -*- coding: utf-8 -*-

import logging

class SplunkLogger:
  """
  Класс-логер
  лог пишет в файл, указанный в конфигурационном файле в секции [SplunkGate].LogPath
  """

  logger = None
  config = {}


  def __init__(self, config):
    """
    Инициализация класса
    В config передается dict, содежащий конфигурацию SplunkGate 
    """

    self.config = config

    self.logger = logging.getLogger(__name__)
    self.logger.setLevel(logging.INFO)
    handler = logging.FileHandler(self.config['splunkgate.logpath'] + '/' + 'splunkgate.log')
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s|%(name)s|%(levelname)s|%(message)s')
    handler.setFormatter(formatter)
    self.logger.addHandler(handler)


  def getLogger(self):
    """Getter для логера"""

    return self.logger
