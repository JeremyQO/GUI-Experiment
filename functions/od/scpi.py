# -*- coding: utf-8 -*-
"""
Created on Wed Jan 20 10:28:35 2021

@author: Jeremy
"""

"""SCPI access to Red Pitaya."""

import socket

__author__ = "Luka Golinar, Iztok Jeras"
__copyright__ = "Copyright 2015, Red Pitaya"

class Scpi (object):
    """SCPI class used to access Red Pitaya over an IP network."""
    delimiter = '\r\n'

    def __init__(self, host, timeout=None, port=5000):
        """Initialize object and open IP connection.
        Host IP should be a string in parentheses, like '192.168.1.100'.
        """
        self.host    = host
        self.port    = port
        self.timeout = timeout

        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            if timeout is not None:
                self._socket.settimeout(timeout)

            self._socket.connect((host, port))

        except socket.error as e:
            print('SCPI >> connect({:s}:{:d}) failed: {:s}'.format(host, port, e))

    def __del__(self):
        if self._socket is not None:
            self._socket.close()
        self._socket = None

    def close(self):
        """Close IP connection."""
        self.__del__()

    def rx_txt(self, chunksize = 4096):
        """Receive text string and return it after removing the delimiter."""
        msg = ''
        while 1:
            chunk = self._socket.recv(chunksize + len(self.delimiter)).decode('utf-8') # Receive chunk size of 2^n preferably
            msg += chunk
            if (len(chunk) and chunk[-2:] == self.delimiter):
                break
        return msg[:-2]

    def rx_arb(self):
        numOfBytes = 0
        """ Recieve binary data from scpi server"""
        str=''
        while (len(str) != 1):
            str = (self._socket.recv(1))
        if not (str == '#'):
            return False
        str=''
        while (len(str) != 1):
            str = (self._socket.recv(1))
        numOfNumBytes = int(str)
        if not (numOfNumBytes > 0):
            return False
        str=''
        while (len(str) != numOfNumBytes):
            str += (self._socket.recv(1))
        numOfBytes = int(str)
        str=''
        while (len(str) != numOfBytes):
            str += (self._socket.recv(1))
        return str

    def tx_txt(self, msg):
        """Send text string ending and append delimiter."""
        return self._socket.send((msg + self.delimiter).encode('utf-8'))

    def txrx_txt(self, msg):
        """Send/receive text string."""
        self.tx_txt(msg)
        return self.rx_txt()

# IEEE Mandated Commands

    def cls(self):
        """Clear Status Command"""
        return self.tx_txt('*CLS')

    def ese(self, value: int):
        """Standard Event Status Enable Command"""
        return self.tx_txt('*ESE {}'.format(value))

    def ese_q(self):
        """Standard Event Status Enable Query"""
        return self.txrx_txt('*ESE?')

    def esr_q(self):
        """Standard Event Status Register Query"""
        return self.txrx_txt('*ESR?')

    def idn_q(self):
        """Identification Query"""
        return self.txrx_txt('*IDN?')

    def opc(self):
        """Operation Complete Command"""
        return self.tx_txt('*OPC')

    def opc_q(self):
        """Operation Complete Query"""
        return self.txrx_txt('*OPC?')

    def rst(self):
        """Reset Command"""
        return self.tx_txt('*RST')

    def sre(self):
        """Service Request Enable Command"""
        return self.tx_txt('*SRE')

    def sre_q(self):
        """Service Request Enable Query"""
        return self.txrx_txt('*SRE?')

    def stb_q(self):
        """Read Status Byte Query"""
        return self.txrx_txt('*STB?')

# :SYSTem

    def err_c(self):
        """Error count."""
        return rp.txrx_txt('SYST:ERR:COUN?')

    def err_c(self):
        """Error next."""
        return rp.txrx_txt('SYST:ERR:NEXT?')
    

class Redpitaya (Scpi):
    def __init__(self, host, timeout=None, port=5000):
        super().__init__(host,timeout,port)
        self.set_decimation(1)
        print(self.idn_q())
        print("Decimation is set to " + self.get_decimation())
        self.set_triggerSource('CH2_PE')
        print("Trigger status is "+ self.get_triggerStatus())
        self.set_averaging('OFF')
        print("Averaging mode is " + self.get_averaging())
        self.set_triggerDelay(0)
        print("Trigger delay at %s ns"%(self.get_triggerDelay()))
        self.set_triggerLevel(0.8) 
        print("Trigger level at %.2f mV"%(float(self.get_triggerLevel())*1000))

    
    def set_decimation(self, d):
        """Set decimation factor."""
        options = (1,8,64,1024,8192,65536)
        if d in options:
            return self.tx_txt('ACQ:DEC '+str(d))
        else:
            print("Please choose decimations from "+str(options))
    
    def get_decimation(self):
        """Get decimation factor"""
        return self.txrx_txt('ACQ:DEC?')
    
    def set_triggerSource(self, s):
        """Disable triggering, trigger immediately or set trigger source & edge."""
        options = ("DISABLED", "NOW", "CH1_PE", "CH1_NE", "CH2_PE", "CH2_NE", "EXT_PE", "EXT_NE", "AWG_PE", "AWG_NE")
        if s in options:
            return self.tx_txt('ACQ:TRIG '+s)
        else:
            print("Please choose source from "+str(options))
            
    def get_triggerStatus(self):
        """Get trigger status. If DISABLED -> TD else WAIT."""
        return self.txrx_txt('ACQ:TRIG:STAT?')
    
    def set_averaging(self, t):
        """Enable/disable averaging."""
        options = ('ON', "OFF")
        if t in options:
            return self.tx_txt('ACQ:AVG '+t)
        else:
            print("Please choose average from "+str(options))
            
    def get_averaging(self):
        """Get averaging status."""
        return self.txrx_txt('ACQ:AVG?')
  
    def get_triggerDelay(self):
        """Get trigger delay in ns.""" 
        return self.txrx_txt("ACQ:TRIG:DLY:NS?")
    
    def set_triggerDelay(self, t):
        """Set trigger delay in ns."""
        return self.tx_txt("ACQ:TRIG:DLY:NS" +str(t))
    
    def get_triggerLevel(self):
        """Get trigger level in V."""
        return self.txrx_txt('ACQ:TRIG:LEV?')
    
    def set_triggerLevel(self, lvl):
        """Set trigger level in V."""
        return self.tx_txt('ACQ:TRIG:LEV '+ str(lvl))
    
    def get_data(self,start, end, source):
        return self.txrx_txt('ACQ:SOUR%i:GET:DATA:%i:%i?'%(int(source), int(start), int(end)))
    
    def get_fullBuffer(self,s):
        """
        Read full buf.
        Size starting from oldest sample in buffer (this is first sample after trigger delay).
        Trigger delay by default is set to zero (in samples or in seconds).
        If trigger delay is set to zero it will read full buf. size starting from trigger.
        """
        return self.txrx_txt("ACQ:SOUR%i:DATA?"%(s))
    
    def start_aquisition(self):
        """Starts acquisition."""
        return self.tx_txt('ACQ:START')
    
    def stop_aquisition(self):
        """Stops acquisition."""
        return self.tx_txt('ACQ:STOP')

    def get_trace (self, channel, trigger, decimation = 1):
        self.start_aquisition()
        self.set_triggerSource('CH%i_PE'%(trigger))
        while 1:
            self.tx_txt('ACQ:TRIG:STAT?')
            if self.rx_txt() == 'TD':
                break
        
        self.tx_txt('ACQ:SOUR%i:DATA?'%(channel))
        buff_string = self.rx_txt()
        buff_string = buff_string.strip('{}\n\r').replace("  ", "").split(',')
        buff = list(map(float, buff_string))
        self.sampling_rate = (len(buff)/13*100000)
        return buff 
            
    
if __name__ == "__main__":
    rp = Redpitaya("132.77.55.19")

    import matplotlib.pyplot as plt
    
    data = rp.get_trace(channel=1,trigger=1)
    
    plt.plot(data)
    plt.ylabel('Voltage')
    plt.show()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    