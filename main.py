from kivy.uix.widget import Widget
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
import socket
from socket import error as socket_error
import binascii
from datetime import datetime

Builder.load_string("""
<MyBoxLayout>:
    id: root_layout
    
    BoxLayout:
        size: root.size
        pos: root.pos
        
        orientation: 'vertical'
        Label:
            text: 'BeamerControl'
            width: 100
            font_size: 30
            bold: False
            halign:  'center'
            valign: 'top'
            #size_hint: 1, .1
        
        GridLayout:
            cols: 2
            rows: 1
            
            Label:
                text_size: self.size
                text: 'connection status: '
                font_size: 30
                bold: False
                halign:  'left'
                valign: 'top'
                size_hint: 1, .1
                
            Label:
                id: idConnStatus
                text_size: self.size
                text: root_layout.txtConnectionStatus
                font_size: 30
                bold: True
                color: 0, 1, 0, 1
                halign:  'center'
                valign: 'top'
                size_hint: 1, .1
        Label:
            text: ''
            font_size: 10
            halign: 'center'
            valign: 'top'
            size_hint: 1, .08
        
        GridLayout:
            cols: 2
            rows: 1
            Button:
                text: 'ON'
                font_size: 30
                background_color: 0, 1, 0, 1
                on_release: root.press_on()
            Button:
                text: 'OFF'
                font_size: 30
                background_color: 1, 0, 0, 1
                on_press: root.press_off()
                
""")

strConnectionStatus = 'initiated'
rootLayout = None

class BeamerControl():

    global strConnectionStatus

    def powerOn(self, *args):
        print('Power ON')
        print('connectionStatus: ', strConnectionStatus)
        try:
            if strConnectionStatus == 'Online':
                print('turn on')
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)

                # Connect to the beamer
                sock.connect(('192.168.100.5', 20554))
                data = sock.recv(1024)
                sock.send(b'PJREQ')

                # Turn the beamer on
                sock.send(b'\x21\x89\x01\x50\x57\x31\x0a')

                # Close the socket
                sock.close()

        except socket.timeout:
            print('Timeout!')
            self.ids.idConnStatus.text = 'Offline'

    def powerOff(self, *args):
        print('Power OFF')
        print('connectionStatus: ', strConnectionStatus)

        try:
            if strConnectionStatus == 'Online':
                print('turn off')
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)

                # Connect to the beamer
                sock.connect(('192.168.100.5', 20554))
                data = sock.recv(1024)
                sock.send(b'PJREQ')

                # Turn the beamer on
                sock.send(b'\x21\x89\x01\x50\x57\x30\x0a')

                # Close the socket
                sock.close()

        except socket.timeout:
            print('Timeout!')


    def checkConnection(self, *args):
        print(datetime.now().strftime("%H:%M:%S"), ' :Connection check')

        global strConnectionStatus
        global rootLayout

        try:
            # Set up the TCP/IP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)

            # Connect to the beamer
            sock.connect(('192.168.100.5', 20554))

            # Wait for the PJ_OK packet
            data = sock.recv(1024)
            if data == b'PJ_OK':
                print('PJ_OK received')
                sock.send(b'PJREQ')
                data = sock.recv(1024)
                print(data.decode('utf-8'))
            else:
                print('Error: PJ_OKPJN not received')

            # Check connection in standby
            sock.send(b'\x21\x89\x01\x00\x00\x0a')
            data = sock.recv(1024)

            if binascii.hexlify(data).decode() == '06890100000a':
                print('Connection established')
                strConnectionStatus = 'ON'
                print(strConnectionStatus)

                if rootLayout != None:
                    rootLayout.ids.idConnStatus.text = 'Online'
                    strConnectionStatus = 'Online'
                else:
                    strConnectionStatus = 'Online'
            else:
                print('No connection')
                strConnectionStatus = 'OFF'

            # Close the socket
            sock.close()
        except ConnectionError as serr:
            print('serr:', serr.errno)
            if serr.errno == 111:
                print('Connection Refused')
        except socket.timeout:
            print('Timeout!')
            if rootLayout != None:
                rootLayout.ids.idConnStatus.text = 'Offline'
                strConnectionStatus = 'Offline'
            else:
                strConnectionStatus = 'Offline'


class MyBoxLayout(Widget):
    global strConnectionStatus
    txtConnectionStatus = strConnectionStatus

    def __init__(self, **kwargs):
        super(MyBoxLayout, self).__init__(**kwargs)
        self.timer = Clock.schedule_interval(BeamerControl.checkConnection, 30)

    def press_off(self):
        print('PRESS:Connection status: ', strConnectionStatus)
        BeamerControl.powerOff(self)

    def press_on(self):
        print('PRESS:Connection status: ', strConnectionStatus)
        BeamerControl.powerOn(self)




class BeamerControlApp(App):
    global strConnectionStatus


    def build(self):
        self.title = 'BeamerControl'
        BeamerControl.checkConnection(self)
        global rootLayout
        rootLayout = MyBoxLayout()
        return rootLayout

    def on_start(self, **kwargs):
        self.root.ids.idConnStatus.text = strConnectionStatus


if __name__ == '__main__':
    BeamerControlApp().run()