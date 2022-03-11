import os
import serial
import time
import threading
import struct
from CRC16_class import CRC16

crc16 = CRC16()

###########################################################
class UART_Dev:
    ############## Private Methods ###############
    def __init__(self, port, baudrate):
        self.baudrate = baudrate
        self.port = port
        self.UUT = serial.Serial(port, baudrate, timeout = 3)
        self.header_bytes = 2
        self.packet_type_bytes = 2
        self.payload_len_bytes = 1
        self.crc_bytes = 2
        #self.thread_read = threading.Thread(target=self.read_msg)
        #self.thread_get = threading.Thread(target=self.get_msg)


    # appends Header and Calculates CRC on data
    # data should have packet_type + payload_len + payload
    def _create_packet(self, data):
        header = [0x55, 0x55]
        packet = []

        packet = packet + header
        packet = packet + data
        
        crc = crc16.crcb(data)
        crc_hex = hex(crc)[2:]

        # CRC has to be 4 char long + odd length strings dont go through bytearray.fromhex()
        if(len(crc_hex) < 4):
            for i in range(4-len(crc_hex)):
                crc_hex = "0"+crc_hex

        crc_bytes = bytearray.fromhex(crc_hex)
        packet.extend(crc_bytes)

        data = packet
        # At this point, data is ready to send to the UUT
        return data

    # returns Packet_type, Payload_length, payload
    def _unpacked_response(self):
        str_list = self.read_response()
        packet_type = ""
        payload_length = ""
        payload = ""

        # when serial read times out, str_list is empty
        if not str_list:
            return packet_type, payload_length, payload
        # serial read was succesful
        else:
            packet_type = str_list[0]
            payload_length = str_list[1]
            payload = str_list[2]
            return packet_type, payload_length, payload

    # appends Header and Calculates CRC on data
    # data should have packet_type + payload_len + payload
    def _send_message(self, data):
        self.UUT.write(self._create_packet(data))

    ############## Public Methods ###############

    # Reads raw data from the UUT
    # Returns list of strings [Packet_type, Payload_length, payload]
    # Returns empty list in case of timeout
    def read_response(self, message_type, timeout = 3):
        t0 = time.time()
        while True:
            data = self.UUT.read(1)
            
            if(data == b'\x55'):
                data = self.UUT.read(1)
                if(data == b'\x55'):
                    packet_list = []
                    
                    #once header found, read other fields from the packet
                    packet_type = self.UUT.read(self.packet_type_bytes)
                    if packet_type == bytes(message_type):                   
                        packet_list.append(packet_type)
         
                        payload_size = self.UUT.read(self.payload_len_bytes)
                        packet_list.append(payload_size)
                        payload_size = struct.unpack('B',payload_size)[0] 
                        #print('payload_size:', payload_size)
                        packet_list.append(self.UUT.read(payload_size))
                        
                        crc_bytes = self.UUT.read(self.crc_bytes)
                        crc_calc_val = struct.unpack('>H', crc_bytes)[0]

                        data_bytes = packet_list[0] + packet_list[1] + packet_list[2]
                        crc_val = crc16.crcb(data_bytes)
                        # print('crc_calc_val:', crc_calc_val, 'crc_val:', crc_val)
                        if crc_calc_val == crc_val:                        
                            #print('packet_list:', packet_list)
                            return packet_list
                        else:
                            print("crc check error.\n")
                            return None
                    else:                       
                        payload_size = self.UUT.read(self.payload_len_bytes)
                        payload_size = struct.unpack('B',payload_size)[0]
                        
                        nbytes = self.UUT.inWaiting()
                        if nbytes >= payload_size + 2:
                            indata = self.UUT.read(payload_size+2)                            
                        else:
                            self.UUT.read(nbytes)
                            
                            
            if(time.time() - t0 > timeout):
                #print("read timeout:", time.time() - t0)
                return None


    def sensor_command(self, message=[]):
        
        for i in range(3):
            self.UUT.flushInput()
            
            # Retrive any unread bytes in buffer
            nbytes = self.UUT.inWaiting()
            if nbytes > 0:
                indata = self.UUT.read(nbytes)
            #rint final_packet
            # Write command to sensor
            
            self.UUT.write(self._create_packet(message))
            self.UUT.flush() 

            # Read Response
            response = self.read_response(message[0:2])
            if response:
                break
   

        if response:
            return response
        else:
            print("Error: No response Received in sensor_commnd")
            return None

    # returns true if ping was successful
    def ping_device(self):
        ping = []
        ping.append("PK")
        ping.append(0x00)
        self._send_message(ping)
        pt,pll,pl = self._unpacked_response()
        if(pt == "PK"):
            return True
        else:
            return False

    def UART_close(self):
        self.UUT.close()

    def get_serial_number(self):
        message = []
        msg_type = [0x70, 0x47]  #pG
        msg_len = 0x00        
        
        message += msg_type
        message.append(msg_len)
        response = self.sensor_command(message)
        if response and response[2]:
            text_str = self._format_string(response[2])
            text = text_str.split(' ')

            serial_number = int(text[4][3:], 16)
            model_string = text[1]
            version = text[3]

            return serial_number, model_string, version
        else:
            print("uart ping failed")
            os._exit(1)
        

    def _format_string(self, data_buffer):
        parsed = bytearray(data_buffer) if data_buffer and len(
            data_buffer) > 0 else None

        formatted = ''
        if parsed is not None:
            try:
                formatted = str(struct.pack(
                        '{0}B'.format(len(parsed)), *parsed), 'utf-8')
            except UnicodeDecodeError:
                APP_CONTEXT.get_logger().logger.error('Parse data as string failed')
                formatted = ''

        return formatted
        