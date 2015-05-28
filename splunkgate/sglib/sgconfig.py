# -*- coding: utf-8 -*-

import ConfigParser

class SplunkConfig:
  """Класс конфигурации SplunkGate"""

  config = {}

  def __init__(self, configFile):
    """
    Инициализация класса
    В configFile передается dict, содежащий конфигурацию SplunkGate 
    """

    try:
      cfg = ConfigParser.ConfigParser()
      cfg.read(configFile)
      self.config['esb.routeId'] = cfg.get('ESB', 'RouteID', '')
      self.config['esb.serviceId'] = cfg.get('ESB', 'ServiceID', '')
      self.config['esb.login'] = cfg.get('ESB', 'Login', '')
      self.config['esb.password'] = cfg.get('ESB', 'Password', '')
      self.config['esb.host'] = cfg.get('ESB', 'Host', '')
      self.config['esb.url'] = cfg.get('ESB', 'URL', '')
      
      self.config['splunk.logpath'] = cfg.get('Splunk', 'LogPath', '')
      self.config['splunk.debug'] = cfg.getboolean('Splunk', 'DebugAlerts')
      servers = cfg.get('Splunk', 'Servers', '').split('\n')
      serverProject = {}
      for server in servers:
        s = server.split(':')
        serverProject[s[0].strip()] = s[1].strip()
        self.config['splunk.servers'] = serverProject

      self.config['splunkgate.logpath'] = cfg.get('SplunkGate', 'LogPath', '')
      self.config['splunkgate.workpath'] = cfg.get('SplunkGate', 'WorkPath', '')
      self.config['splunkgate.сreateSnapshot'] = cfg.getboolean('SplunkGate', 'CreateSnapshot')
      self.config['splunkgate.readOnlyFirstElement'] = cfg.getboolean('SplunkGate', 'ReadOnlyFirstElement')
      self.config['splunkgate.db'] = cfg.get('SplunkGate', 'Database')

    except Exception, e:
      print 'Unsuccess get SplunkGate configuration: ' + str(e)


  def getConfigParams(self):
    """Getter для dict с конфигурационными параметрами"""
    return self.config