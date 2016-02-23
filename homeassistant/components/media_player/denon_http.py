""""
homeassistant.components.media_player.denon_http
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Provides an interface to the Denon AVR http API

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/media_player.denon_http/
"""
import logging
import requests
from xml.etree import ElementTree

from homeassistant.components.media_player import (
	MEDIA_TYPE_MUSIC, SUPPORT_NEXT_TRACK, SUPPORT_PAUSE,
    SUPPORT_PLAY_MEDIA, SUPPORT_PREVIOUS_TRACK, SUPPORT_SEEK, SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON, SUPPORT_VOLUME_MUTE, SUPPORT_VOLUME_SET,
    MediaPlayerDevice)
from homeassistant.const import (
    CONF_HOST, STATE_IDLE, STATE_OFF, STATE_ON, STATE_PAUSED, STATE_PLAYING)

_LOGGER = logging.getLogger(__name__)

SUPPORT_DENON_HTTP = SUPPORT_PAUSE | SUPPORT_VOLUME_SET | SUPPORT_VOLUME_MUTE | \
    SUPPORT_PREVIOUS_TRACK | SUPPORT_NEXT_TRACK | SUPPORT_SEEK | \
    SUPPORT_PLAY_MEDIA
def setup_platform(hass, config, add_devices, discovery_info=None):
	""" Sets up the Denon Platform """
	if not config.get(CONF_HOST):
		_LOGGER.error(
			"Missing required configuration items in %s: %s",
			DOMAIN,
			CONF_HOST)
		return False
	denonHttp = DenonHttpDevice(
		config.get("name","DENON AVR"),
		config.get("host")
	)
	if denonHttp.update():
		add_devices([denon_http])
		return True
	else:
		return False

class DenonHttpDevice(MediaPlayerDevice):
	""" Represents a Denon AVR device """
	# pylint: disable=too-many-public-methods, abstract-method
	def __init__(self, name, host):
		self._name = name
		self._host = host
		self._pwstate = "PWSTANDBY"
		self._volume = 0
		self._muted = False
		self._mediasource = ""
		

	def http_request_post(self,endpoint,obj):
		
		"""
		endpoint example: NetAudio/index.put.asp
		obj example: {
			cmd0: "PutMasterVolumeBtn/>",
			cmd1: "aspMainZone_WebUpdateStatus/"
		}
		"""
		response = requests.post("http://"+self._host+"/"+endpoint,payload=obj)
		return ElementTree.fromstring(response.content)
	def http_request_get(self,endpoint):
		"""
		curl 'http://192.168.0.184/goform/formNetAudio_StatusXml.xml?_=1456233183385&ZoneName=MAIN+ZONE' -H 'Cookie: ZoneName=MAIN%20ZONE' -H 'Accept-Encoding: gzip, deflate, sdch' -H 'Accept-Language: en-US,en;q=0.8,nl;q=0.6' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.109 Safari/537.36' -H 'Accept: */*' -H 'Referer: http://192.168.0.184/NetAudio/index.html' -H 'X-Requested-With: XMLHttpRequest' -H 'Connection: keep-alive' --compressed
		curl 'http://192.168.0.184/goform/formMainZone_MainZoneXml.xml?_=1456233692386' -H 'Cookie: ZoneName=MAIN%20ZONE' -H 'Accept-Encoding: gzip, deflate, sdch' -H 'Accept-Language: en-US,en;q=0.8,nl;q=0.6' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.109 Safari/537.36' -H 'Accept: */*' -H 'Referer: http://192.168.0.184/MainZone/index.html' -H 'X-Requested-With: XMLHttpRequest' -H 'Connection: keep-alive' --compressed
		"""
		response = requests.get("http://"+self._host+"/"+endpoint)
		return ElementTree.fromstring(response.content)
	def update(self):
		self._formNetAudio_Statusxml = self.http_request_get('goform/formNetAudio_StatusXml.xml')
		self._formMainZone_MainZonexml = self.http_request_get('goform/formMainZone_MainZoneXml.xml')
		self._powerState = self._formMainZone_MainZonexml.findall("Power/value")[0].text
		self._MuteState = self._formMainZone_MainZonexml.findall("Mute/value")[0].text
		self._volumeState = self._formMainZone_MainZonexml.findall("MasterVolume/value")[0].text
		self._mediaSourceData = [ d.text for d in self._formNetAudio_Statusxml.findall("szLine/value") ]
		_LOGGER.info("%s %s %s",self._powerState,self._MuteState,self._volumeState)
		_LOGGER.info(self._mediaSourceData)
	@property
	def name(self):
		""" Returns the name of the device. """
		return self._name
	@property
	def state(self):
		""" Returns the state of the device. """
		if self._powerState == "STANDBY":
			return STATE_OFF
		if self.powerState == "ON":
			return STATE_ON
		return STATE_UNKNOWN

