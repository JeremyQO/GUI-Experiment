# -*- coding: utf-8 -*-
import websocket, requests, gzip, json

import numpy as np
import time


class Redpitaya:
    # TODO: use timeout, get rid of port

    def __init__(self, host,got_data_callback = None, timeout=None, trigger_source='EXT', dialogue_print_callback = None):
        """Initialize object and open IP connection.
        Host IP should be a string in parentheses, like '192.168.1.100'.
        """

        self.time = time.time()
        # self.print("Initing Redpitayas class instance (%s)..." %host)
        self.host = host
        self.timeout = timeout
        self.new_parameters = {}
        self.received_parameters = {'new_parameters': True} # 'new_parameters' set to true, in order to redraw the plot for the first time
        self.sampling_rate = 125e6
        self.connected = False
        self.ws = None

        # TODO: delete following two lines.
        self.set_triggerSource(trigger_source)  # By default, EXT
        self.set_triggerLevel(1000)
        self.set_dataSize(1024)

        self.print = dialogue_print_callback
        if dialogue_print_callback is None:
            self.print = self.print_data

        # Set data-callback; i.e., what to do when we get data from RP
        self.got_data_callback = got_data_callback
        if self.got_data_callback is None:
            self.got_data_callback = self.print_data
            self.print('Warning! got_data_callback not given. Data will be printed out by default.', color = 'red')

        """ First, make sure the Red Pitaya is set to the correct app (on the device!)"""
        appName = 'scopegenpro'  # This is the default app name of scope on RP. It is the scope app, which can be controlled using a web-socket.
        appConnectURL = 'http://%s/bazaar?start=%s' % (self.host, appName)
        try:
            response = requests.get(appConnectURL)
            self.print(str(response))  # TODO: check this repsonse should be 200, otherwise throw exception(?)
        except Exception as e:
            self.print('Connection to %s failed.' % (appConnectURL), color='red')
            self.print(str(e))
            self.connected = False
            return


        """ Then, connect to the RP socket"""
        try:
            wsURL = "ws://%s/wss" % str(self.host)
            self.print('Connecting to %s ' % wsURL)
            self.ws = websocket.WebSocketApp(wsURL,
                                             on_message=self.on_message,on_close=self.on_close,on_error=self.on_error)# on_open=on_open,)
            self.connected = True
        except Exception as e:
            self.print('Connect({:s}) failed: {:s}'.format(host, str(e)), color = 'red')

    def __del__(self):
        #self.print('Deleting Redpitaya object! \nProbably because connection failed.')
        if self.ws is not None:
            self.ws.close()
        self.ws = None

    def run(self):
        if self.ws and self.connected:
            self.ws.run_forever()

    def updateParameters(self):
        # Check if there's anything to update
        if self.new_parameters == {}:
            return
        self.new_parameters['in_command'] = {'value': 'send_all_params'}  # Not sure if this addition is obligatory, but it's always there for some reason, so why not.
        # I *THINK* it means socket responds with all parameters
        load = json.dumps({'parameters': self.new_parameters})
        # Zero-out parameters to change.
        self.new_parameters = {}
        self.ws.send(load)  # .encode())

    def on_message(self, ws, message):
        self.updateParameters()  # Update any pending parameters change

        # @messgae is (probably) unicode string represting compressed data.
        # This data must be decompressed (using gzip), then decoded (utf-8),
        # resulting in a JSON dictionary.
        data_text = gzip.decompress(message)
        data = json.loads(data_text.decode('utf-8'))

        if 'signals' in data:
            ch1_values = data['signals']['ch1']['value']
            ch2_values = data['signals']['ch2']['value']
            self.got_data_callback(data = [ch1_values,ch2_values], parameters = self.received_parameters) # update scope with new data!
            self.received_parameters['new_parameters'] = False # After updating scope, with the existing parameters, these are not considered new anymore (this is for efficiency)
        elif 'parameters' in data:
            if 'OSC_TIME_SCALE' in data['parameters']:
                self.received_parameters = data['parameters']
                self.received_parameters['new_parameters'] = True
        else:
            self.print('Unexpected response from RP: \n%s' %data, color = 'red')

    def on_error(self, ws, error):
        self.print('RedPitayaWebsocket error: %s' %str(error), color = 'red')

    def on_close(self, ws, close_status_code, close_msg):
        # Be    cause on_close was triggered, we know the opcode = 8
        print("on_close args:")
        if close_status_code or close_msg:
            print("close status code: " + str(close_status_code))
            print("close message: " + str(close_msg))
        print("### closed ###")

    def close(self):
        """Close IP connection."""
        self.__del__()

    # Regular print to console
    def print_data(self, data, parameters, color, *args):
        print(data)

    def set_dataSize(self, s =1024):
        # Size of data vector rceived from RP
        if s < 1024 or s > 16384:
            self.print('Data size must be 1024-16384!', color = 'red')
            return
        self.new_parameters['OSC_DATA_SIZE'] = {'value': s}

    def set_triggerSource(self, s):
        """Disable triggering, trigger immediately or set trigger source & edge."""
        #options = ("DISABLED", "NOW", "CH1_PE", "CH1_NE", "CH2_PE", "CH2_NE", "EXT_PE", "EXT_NE", "AWG_PE", "AWG_NE")
        options = ("CH1", "CH2", "EXT")
        if s in options:
            self.new_parameters['OSC_TRIG_SOURCE'] = {'value': options.index(s)}
        else:
            self.print("Please choose source from " + str(options), color = 'red')
        self.set_triggerSweep()

    def set_triggerSweep(self, s='NORMAL'):
        options = ('AUTO', 'NORMAL', 'SINGLE')
        if s in options:
            print('Setting trigger-sweep to %s' %s)
            self.new_parameters['OSC_TRIG_SWEEP'] = {'value': options.index(s)}
            self.new_parameters['OSC_RUN'] = {'value': True}
        else:
            self.print("Please choose source from " + str(options), color = 'red')

    def set_triggerLevel(self, lvl):
        """Set trigger level in mV.""" # mV???
        if np.abs(lvl) < 2000:
            self.new_parameters['OSC_TRIG_LEVEL'] = {'value':lvl}
        else:
            self.print('Trigger level must be < 2000', color = 'red')  # Not sure about trigger limit. it's thus in original code

    def set_triggerDelay(self, t):
        """Set trigger delay in mili-sec."""
        self.new_parameters['OSC_TIME_OFFSET'] = {'value': t}

    def set_timeScale(self, t):
        """Set time scale in mili-sec."""
        # Note: this is time scale per 1 division. There are 10 divisions (!)
        self.new_parameters['OSC_TIME_SCALE'] = {'value': str(t)} # note strange: this (float) is converted to string

    def set_yScale(self, t, ch = 1):
        if ch < 1 or ch > 4: return
        """Set time scale in mili-sec."""
        # Note: this is y-scale (volt) per 1 division. There are 10 divisions (!)
        self.new_parameters['OSC_CH%d_SCALE' % int(ch)] = {'value': float(t)} # note strange: this (float) is converted to string
        self.print('WARNING: keep this value 1, unless you really know what you are doing.',color='red')

    # set y scale. value is in volts (usually, <1). There are 10 division, so 10 * value gives the limits
    #{"parameters": {"OSC_CH1_SCALE": {"value": 0.1}, "OSC_CH1_OFFSET": {"value": 0},
    #                "in_command": {"value": "send_all_params"}}}


    # set x scale. value is per division, in mSec. There are 10 division, so 10 * value gives the limits
    #{"parameters": {"OSC_TIME_OFFSET": {"value": 0}, "OSC_TIME_SCALE": {"value": "0.0005"},
                    #"in_command": {"value": "send_all_params"}}}

    def get_triggerStatus(self):
        """Get trigger status"""
        trigger_states = ['STOPPED', 'AUTO', 'TRIG\'D', 'WAITING']
        # Trigger state:
        try:
            trigger_info = self.received_parameters['OSC_TRIG_INFO']
            return trigger_states[trigger_info['value']]
        except:
            return 'Unable to retrieve trigger state.'

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
    

    
    def get_triggerLevel(self):
        """Get trigger level in V."""
        return self.txrx_txt('ACQ:TRIG:LEV?')



import matplotlib.pyplot as plt # TODO for debugging

if __name__ == "__main__":
    # rp1 = Redpitaya("rp-f08a95.local")  # sigma +/-
    # rp1 = Redpitaya("127.0.0.1")  # sigma +/-

    # rp2 = Redpitaya("rp-f08c22.local")  # Pi
    rp2 = Redpitaya("rp-f08c22.local")  # Pi


