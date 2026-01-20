import network
import socket
import machine

try:
    import logging
except ImportError:
    class logging():
        def __init__(self, *args, **kwargs):
            pass
        
        def __getattr__(self, attr):
            return logging()

log = logging.getLogger(__name__)

def connect(ssid, pwd, force_disconnect=False):
    wlan = network.WLAN()
    wlan.active(True)
  
    if wlan.isconnected():
        log.info("Connected with IP %s", wlan.ipconfig('addr4')[0])
        if force_disconnect:
            wlan.disconnect()
        else:
            return
        
    log.info("Connecting...")
    wlan.connect(ssid, pwd)
    while wlan.status() == network.STAT_CONNECTING:
        machine.idle()

    try:
        if wlan.status() == network.STAT_NO_AP_FOUND:
            raise ValueError("'{}' not found while scanning".format(ssid))
        elif wlan.status() == network.STAT_WRONG_PASSWORD:
            raise ValueError("Wrong password for '{}'".format(ssid))
        elif wlan.status() == network.STAT_CONNECT_FAIL:
            raise ValueError("STAT_CONNECT_FAIL: Could not connect to '{}'.".format(ssid))
        elif wlan.status() == network.STAT_GOT_IP:
            log.info("Connected  to '{}' with IP {}".format(ssid, wlan.ipconfig('addr4')[0]))
    except ValueError as e:
        log.exception(e)
        raise e


def test_online(url='www.micropython.org'):
    log.info('Testing connection to %s ...', url)
    try:
        s = socket.socket()
        s.settimeout(3)
        addr = socket.getaddrinfo(url, 80, 0, socket.SOCK_STREAM)[0][-1]
        s.connect(addr)
        log.info('Device online')
        return True
    except Exception as e:  
        log.warning('Device offline')
        return False
        

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
