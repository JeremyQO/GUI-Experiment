# -*- coding: utf-8 -*-
"""
Created on Wed Jan 20 10:28:35 2021

@author: Jeremy

SCPI access to Red Pitaya.
"""

import socket
import numpy as np
import time
#from functions.od.RSCurrentGenerator.RSCurrentGenerator import RSCurrentGenerator


class Scpi (object):
    """SCPI class used to access Red Pitaya over an IP network."""
    delimiter = '\r\n'

    def __init__(self, host, timeout=None, port=5000):
        """Initialize object and open IP connection.
        Host IP should be a string in parentheses, like '192.168.1.100'.
        """
        self.host = host
        self.port = port
        self.timeout = timeout

        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            if timeout is not None:
                self._socket.settimeout(timeout)

            self._socket.connect((host, port))

        except socket.error as e:
            print(host,':', port)
            print('SCPI >> connect({:s}:{:d}) failed: {:s}'.format(host, port, e))

    def __del__(self):
        if self._socket is not None:
            self._socket.close()
        self._socket = None

    def close(self):
        """Close IP connection."""
        self.__del__()

    def rx_txt(self, chunksize=4096):
        """Receive text string and return it after removing the delimiter."""
        msg = ''
        while 1:
            chunk = self._socket.recv(chunksize + len(self.delimiter)).decode('utf-8')  # Receive chunk size of 2^n preferably
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
        return self.txrx_txt('SYST:ERR:COUN?')

    def err_n(self):
        """Error next."""
        return self.txrx_txt('SYST:ERR:NEXT?')
    

class Redpitaya (Scpi):
    def __init__(self, host, timeout=None, port=5000, decimation=8, trigger_delay=0, trigger_source='EXT_PE'):
        super().__init__(host, timeout, port)
        self.sampling_rate = 125e6
        self.decimation = decimation
        self.trigger_delay = trigger_delay
        self.set_decimation(decimation)
        # self.set_triggerDelay(trigger_delay)
        print(self.idn_q())
        print("Decimation is set to " + self.get_decimation())
        # self.set_triggerSource('CH2_PE')
        self.trigger_source = trigger_source
        self.set_triggerSource(self.trigger_source)  # By default, we trigger on the default DIO0_P
        print("Trigger status is " + self.get_triggerStatus())
        self.set_averaging('OFF')
        print("Averaging mode is " + self.get_averaging())
        self.set_triggerDelay(trigger_delay)
        print("Trigger delay at %s ns" % (self.get_triggerDelay()))
        self.set_triggerLevel(1000)
        print("Trigger level at %.2f mV" % (float(self.get_triggerLevel())*1000))
        self.tx_txt('OUTPUT1:STATE OFF')
        print("Output 1 is OFF")
        self.tx_txt('OUTPUT2:STATE OFF')
        print("Output 2 is OFF")

    def set_decimation(self, d):
        """Set decimation factor."""
        options = (1, 8, 64, 1024, 8192, 65536)
        if d in options:
            newTriggDelay = self.trigger_delay/self.decimation * d
            self.set_triggerDelay(newTriggDelay)
            self.decimation = d
            return self.tx_txt('ACQ:DEC '+str(d))
        else:
            print("Please choose decimation from "+str(options))
    
    def get_decimation(self):
        """Get decimation factor"""
        return self.txrx_txt('ACQ:DEC?')
    
    def set_triggerSource(self, s):
        """Disable triggering, trigger immediately or set trigger source & edge."""
        options = ("DISABLED", "NOW", "CH1_PE", "CH1_NE", "CH2_PE", "CH2_NE", "EXT_PE", "EXT_NE", "AWG_PE", "AWG_NE")
        if s in options:
            self.trigger_source = s
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
        self.trigger_delay = t
        return self.tx_txt("ACQ:TRIG:DLY:NS " +str(t))
    
    def get_triggerLevel(self):
        """Get trigger level in V."""
        return self.txrx_txt('ACQ:TRIG:LEV?')
    
    def set_triggerLevel(self, lvl):
        """Set trigger level in V."""
        return self.tx_txt('ACQ:TRIG:LEV '+ str(lvl) + ' mV')
    
    def get_data(self,start, end, source):
        return self.txrx_txt('ACQ:SOUR%i:GET:DATA:%i:%i?'%(int(source), int(start), int(end)))
    
    def get_fullBuffer(self, s):
        """
        Read full buf.
        Size starting from oldest sample in buffer (this is first sample after trigger delay).
        Trigger delay by default is set to zero (in samples or in seconds).
        If trigger delay is set to zero it will read full buf. size starting from trigger.
        """
        return self.txrx_txt("ACQ:SOUR%i:DATA?"%(s))
    
    def start_acquisition(self):
        """Starts acquisition."""
        return self.tx_txt('ACQ:START')
    
    def stop_acquisition(self):
        """Stops acquisition."""
        return self.tx_txt('ACQ:STOP')

    def get_trace(self, channel):
        self.start_acquisition()
        self.set_triggerSource(self.trigger_source)
        while 1:
            self.tx_txt('ACQ:TRIG:STAT?')
            if self.rx_txt() == 'TD':
                break
        #RSCurrentGenerator.Config_Currents(0.2, 0.05, 1)  # assaf added
        self.tx_txt('ACQ:SOUR%i:DATA?' % (channel))
        buff_string = self.rx_txt()
        buff_string = buff_string.strip('{}\n\r').replace("  ", "").split(',')
        buff = list(map(float, buff_string))
        self.sampling_rate = (len(buff)/13*100000) / self.decimation
        return buff

    def get_traces(self):
        self.start_acquisition()
        self.set_triggerSource(self.trigger_source)
        while 1:
            self.tx_txt('ACQ:TRIG:STAT?')
            if self.rx_txt() == 'TD':
                break

        self.tx_txt('ACQ:SOUR%i:DATA?' % (1))
        buff_string = self.rx_txt()
        buff_string = buff_string.strip('{}\n\r').replace("  ", "").split(',')
        buff1 = list(map(float, buff_string))

        self.tx_txt('ACQ:SOUR%i:DATA?' % (2))
        buff_string = self.rx_txt()
        buff_string = buff_string.strip('{}\n\r').replace("  ", "").split(',')
        buff2 = list(map(float, buff_string))

        self.sampling_rate = (len(buff1) / 12.5 * 100000) / self.decimation
        return buff1, buff2

    def get_fullbufferFormated(self, s):
        buff_string = self.get_fullBuffer(s)
        buff_string = buff_string.strip('{}\n\r').replace("  ", "").split(',')
        buff1 = list(map(float, buff_string))
        return buff1

    def outputSin(self, ampl=0.9, freq=10000, output=1):
        wave_form = 'sine'
        self.tx_txt('GEN:RST')
        self.tx_txt('SOUR%s:FUNC ' % output + str(wave_form).upper())
        self.tx_txt('SOUR%s:FREQ:FIX ' % output + str(freq))
        self.tx_txt('SOUR%s:VOLT ' % output + str(ampl))

        # Enable output
        self.tx_txt('OUTPUT%s:STATE ON' % output)


# def acquireHomodyne(rp, s):
#     data = []
#     for i in range(100):
#         d = rp.get_fullbufferFormated(s)
#         data.append(d)
#         time.sleep(0.01)
#         print(i)
#     if s == 1:
#         np.savetxt("homodyne_electronics_CH1.txt", data)
#     if s == 2:
#         np.savetxt("homodyne_electronics_CH2.txt", data)

class redPitayaCluster :
    def __init__(self, trigger_delay=-40000, decimation=8):
        print("Connecting to rp-f08a95.local")
        # self.Sigma = Redpitaya("rp-f08a95.local", trigger_delay=trigger_delay, decimation=decimation)  # sigma +/-
        self.Sigma = Redpitaya("rp-f08c36.local", trigger_delay=trigger_delay, decimation=decimation)  # sigma +/-
        print("Connecting to rp-f08c22.local")
        self.Pi = Redpitaya("rp-f08c22.local", trigger_delay=trigger_delay, decimation=decimation)  # Pi
        print("Connecting to rp-f0629e.local")
        self.OD = Redpitaya("rp-f0629e.local", trigger_delay=trigger_delay, decimation=decimation, trigger_source='EXT_NE')  # OD
        self.rplist = [self.OD, self.Sigma, self.Pi]
        self.triggerDelay = trigger_delay
        self.decimation = decimation
        self.sampling_rate = 125e6

    def set_triggerDelay(self, t):
        for rp in self.rplist:
            rp.set_triggerDelay(t)
            self.triggerDelay = t

    def set_decimation(self, d):
        for rp in self.rplist:
            rp.set_decimation(d)
        # self.set_triggerDelay(self.triggerDelay / d)
        self.decimation = d
        self.triggerDelay = self.Sigma.trigger_delay

    def set_triggerSource(self, s):
        """Disable triggering, trigger immediately or set trigger source & edge."""
        for rp in self.rplist:
            rp.set_triggerSource(s)


    def get_triggerDelay(self):
        """Get trigger delay in ns."""
        return [redp.get_triggerDelay() for redp in self.rplist]

    def get_tracesSlow(self):
        data1_OD, data2_OD = self.OD.get_traces()
        data1_Sigma, data2_Sigma = self.Sigma.get_traces()
        data1_Pi, data2_Pi = self.Pi.get_traces()
        data = [data1_OD,
                data2_OD,
                data1_Sigma,
                data2_Sigma,
                np.array(data1_Sigma) + np.array(data2_Sigma),
                data1_Pi,
                ]
        return data

    def get_traces(self, which=[True, True, True]):
        for el in self.rplist:
            el.start_acquisition()
            el.set_triggerSource(el.trigger_source)
        while 1:
            self.rplist[0].tx_txt('ACQ:TRIG:STAT?')
            if self.rplist[0].rx_txt() == 'TD':
                break
        data = []
        for i, el in enumerate(self.rplist):
            if which[i] is True:
                el.tx_txt('ACQ:SOUR%i:DATA?' % (1))
                buff_string = el.rx_txt()
                buff_string = buff_string.strip('{}\n\r').replace("  ", "").split(',')
                buff1 = list(map(float, buff_string))
                data.append(buff1)
                el.tx_txt('ACQ:SOUR%i:DATA?' % (2))
                buff_string = el.rx_txt()
                buff_string = buff_string.strip('{}\n\r').replace("  ", "").split(',')
                buff2 = list(map(float, buff_string))
                data.append(buff2)
            else:
                data.append(np.zeros(16384))
                data.append(np.zeros(16384))

        self.bufferDuration = (len(data[0]) / self.sampling_rate) * self.rplist[0].decimation
        return data


def get_frequency_shift():
    pass

if __name__ == "__main__":
    # rp1 = Redpitaya("rp-f08a95.local")  # sigma +/-
    # rp1 = Redpitaya("127.0.0.1")  # sigma +/-

    rp2 = Redpitaya("rp-f08c22.local")  # Pi
    # rp3 = Redpitaya("rp-f0629e.local")  # OD
    # rp = redPitayaCluster()
    # a, b = rp2.get_traces()


