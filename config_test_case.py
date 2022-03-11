import os 
import sys
import time
import json
import serial
import struct
import threading
from tqdm import trange, tqdm

parse_dict = {
    'gN': [53, "674E", "self.parse_gN"],
    'gB_part1': [37, "6742", "self.parse_gB_p1"],
    'gB_part2': [33, "6742", "self.parse_gB_p2"]
}

CSYS_dict = {
    'first': [90.0, 0.0, 180.0],
    'second': [0.0, 90.0, -180.0],
    'third': [-90.0, -90.0, -180.0],
    'forth': [0.0, 0.0, 0.0]
}

class ConfigTest:
    def __init__(self, ser, logf):
        self.path = os.getcwd()
        self.ser = ser
        self.get_user_para = True
        self.set_user_para = True
        self.save_user_para = True

        self.restart_user = True
        switch_mode = input("Input Y to use restart command\nInput N to use GPIO repower device\n")
        if switch_mode == 'Y':
            self.reset_user = True
            self.repower = False
        elif switch_mode == 'N':
            self.reset_user = False
            self.repower = True
        else:
            print('The test end')
            os._exit()
        self.command_line = None
        self.result = None
        self.parse = None
        self.success_times = 0
        self.test_logf = logf

        if self.repower is True:
            from GPIO import GPIO_excutor as GPIO
        else:
            print('GPIO is banned')

        with open(self.path + '/setting/setting.json') as json_data:
            self.properties = json.load(json_data)

        with open(self.path + '/setting/backup.json') as json_data_backup:
            self.copy_data = json.load(json_data_backup)
    
    # section 1
    def set_cmd_test(self):
        '''
        set test initiator
        set params to device, then save it and restart, check params
        '''
        test_times = 500
        ser = self.ser
        if ser.isOpen():
            pass
        else:
            ser.open()
        gB_res_size = 37
        for _ in trange(test_times):
            if self.reset_user is True:
                msg_response_reset = self.reset_func(ser, size=gB_res_size)
            if self.set_user_para is True:
                self.set_func(ser)
            if self.save_user_para is True:
                self.save_func(ser)
            if self.restart_user is True:
                self.restart_func(ser)
                ser.flushOutput()
            if self.repower is True:
                self.repower_func()
            if self.get_user_para is True:
                self.get_func(ser, size=gB_res_size, compare_msg=msg_response_reset)
        if self.success_times == test_times:
            print('Configuration test passed, success:{} \n'.format(self.success_times))
            self.test_logf.write(f'test time: {test_times}')
            self.test_logf.write('Configuration test passed, success:{} \n'.format(self.success_times))
            self.test_logf.write('Section 1 is passed')
        else:
            fail_times = test_times - self.success_times
            print('Configuration test failed, fail:{}'.format(fail_times))
            print('Section 2 is finished')
            self.test_logf.write('Configuration test failed, fail:{}'.format(fail_times))
            self.test_logf.write('Section 1 is failed')
        ser.close()
        
    # section 2
    def _restart(self):
        '''
        restart test initiator
        '''
        test_times = 10
        passed_times = 0
        self.test_logf.write("'UUSR cmd' test start(test times:{}):".format(test_times) + '\n')
        ser = self.ser
        if ser.isOpen():
            pass
        else:
            ser.open()
        for i in trange(test_times):
            self.test_logf.write('Turn {}:'.format(i) + '\n')
            sniffer = True
            if self.restart_user is True:
                self.restart_func(ser)
                start_t = time.strftime("%H:%M:%S")
                self.test_logf.write("Send 'UUSR cmd' at time: {}".format(start_t) + '\n')
            while sniffer is True:
                packet_size = 53
                packet_type = parse_dict['gN'][1]
                parse_func = parse_dict['gN'][2]
                gN_msg = self.parse_executor(ser, packet_size, packet_type, parse_func, command_line=None)
                end_time = time.strftime("%H:%M:%S")
                self.test_logf.write('gN_packet is found at: {}'.format(end_time) + '\n')
                self.test_logf.write('gN_packet parse data: {}'.format(gN_msg) + '\n')
                passed_times = passed_times + 1
                sniffer = False
        self.test_logf.write('End of test, passed times is {}'.format(passed_times) + '\n\r')
        if passed_times == test_times:
            self.test_logf.write('Section 2 is passed')
        else:
            self.test_logf.write('Section 2 is failed')
        print('Section 2 is finished\n')

    # section 3
    def CSYS_config_test(self):
        '''
        Coordinate system configuration test
        '''
        ser = self.ser
        if ser.isOpen():
            pass
        else:
            ser.open()
        params = self.properties["initial"]["userParameters"]
        paramsId_lens = len(params)
        for i, (key, value) in enumerate(tqdm(CSYS_dict.items())):
            coordinate = (key, value)
            value_list = coordinate[1]
            for j in range(paramsId_lens):
                if j == 13:
                    self.properties["initial"]["userParameters"][j]["value"] = value_list[0]

                    with open(self.path + '/setting/setting.json', "w+") as fw:
                        json.dump(self.properties, fw, ensure_ascii=False, indent=4)

                if j == 14:
                    self.properties["initial"]["userParameters"][j]["value"] = value_list[1]

                    with open(self.path + '/setting/setting.json', "w+") as fw:
                        json.dump(self.properties, fw, ensure_ascii=False, indent=4)

                if j == 15:
                    self.properties["initial"]["userParameters"][j]["value"] = value_list[2]

                    with open(self.path + '/setting/setting.json', "w+") as fw:
                        json.dump(self.properties, fw, ensure_ascii=False, indent=4)

            if self.set_user_para is True:
                self.set_func(ser)
            if self.save_user_para is True:
                self.save_func(ser)
            
            gB_packet_size = parse_dict['gB_part2'][0]
            command_line = self.get_params()[1]
            packet_type = parse_dict['gB_part2'][1]
            parse_func = parse_dict['gB_part2'][2]

            if self.get_user_para is True: 
                params = self.parse_executor(ser, gB_packet_size, packet_type, parse_func, command_line)
                rotation_rbvx = params[5]
                rotation_rbvy = params[6]
                rotation_rbvz = params[7]
            
            if rotation_rbvx == value_list[0]:
                self.test_logf.write(f'{coordinate[0]}: X-axis is configured successfully' + '\n')
            else:
                self.test_logf.write(f'{coordinate[0]}: X-axis is configured failed' + '\n')
            if rotation_rbvy == value_list[1]:
                self.test_logf.write(f'{coordinate[0]}: Y-axis is configured successfully' + '\n')
            else:
                self.test_logf.write(f'{coordinate[0]}: Y-axis is configured failed' + '\n')
            if rotation_rbvz == value_list[2]:
                self.test_logf.write(f'{coordinate[0]}: Z-axis is configured successfully' + '\n\r')
            else:
                self.test_logf.write(f'{coordinate[0]}: Z-axis is configured failed' + '\n\r')
            
            # reset the json file
            with open(self.path + '/setting/setting.json', "w+") as fw:
                json.dump(self.copy_data, fw, ensure_ascii=False, indent=4)
        
        print('Section 3 is finished')
                        
    def parse_executor(self, ser, size, packet_type, parse_func, command_line):
        '''
        The initiator that parses the target packet
        Get the DEC data
        '''
        # packet_size = 37
        packet_size = size
        sniffer = True
        packet_type = None
        packet_crc = None
        calculated_crc = []
        while sniffer is True:
            read_size = ser.in_waiting
            data = ser.read(read_size)
            if command_line is not None:
                get_command = command_line
                ser.write(bytes(get_command))
            else:
                pass
            for i, _ in enumerate(data):
                lens = len(data)
                header_type = data[i:(i+2)].hex()
                if header_type == '5555' and \
                    lens - i > (packet_size + 1):
                    packet_type = data[(i+2):(i+4)].hex()
                if packet_type == packet_type and \
                    lens - i > (packet_size + 1):
                    # print(data.hex())
                    # self.parser = eval('self.gB_parse_part1')
                    self.parser = eval(parse_func)
                    packet_crc = []
                    crc_f = data[i+packet_size-2]
                    crc_s = data[i+packet_size-1]
                    packet_crc.append(crc_f)
                    packet_crc.append(crc_s)
                    calculated_crc = self.calc_crc(data[(i+2):(i+packet_size-2)])
                if packet_crc == calculated_crc:
                    latest = self.parse_packet(data[(i+2):(i+packet_size-2)])
                    # print(latest)
                    sniffer = False
                    self.reopen_port(ser, 3)
        return latest

    def parse_packet(self, payload):
        data = self.parser(payload[3::])
        return data   

    def parse_gN(self, payload):
        fmt = '<IdBiifBfffHhhh'
        data = struct.unpack(fmt, payload)
        gps_week = data[0]
        time_of_week = data[1]
        pos_mode = data[2]
        latitude = data[3]
        longitude = data[4]
        hight = data[5]
        num_of_SVs = data[6]
        hdop = data[7]
        vdop = data[8]
        tdop = data[9]
        diffage = data[10]
        velocity_north = data[11]
        velocity_east = data[12]
        velocity_up = data[13]

        return gps_week, time_of_week, pos_mode, latitude, longitude, hight, num_of_SVs, hdop, vdop, tdop, \
            diffage, velocity_north, velocity_east, velocity_up

    def parse_gB_p1(self, payload):
        fmt = '<BBBBBBffffff'
        data = struct.unpack(fmt, payload)
        start_byte = data[0]
        end_byte = data[1]

        raw_rate = data[2]
        gnss_rate = data[3]
        INSPVA_rate = data[4]
        INSSTD_rate = data[5]

        pri_lever_arm_x = data[6]
        pri_lever_arm_y = data[7]
        pri_lever_arm_z = data[8]

        vrp_lever_arm_x = data[9]
        vrp_lever_arm_y = data[10]
        vrp_lever_arm_z = data[11]

        return start_byte, end_byte, raw_rate, gnss_rate, INSPVA_rate, INSSTD_rate, pri_lever_arm_x, \
            pri_lever_arm_y, pri_lever_arm_z, vrp_lever_arm_x, vrp_lever_arm_y, vrp_lever_arm_z

    def parse_gB_p2(self, payload):
        fmt = '<BBffffff'
        data = struct.unpack(fmt, payload)
        start_byte = data[0]
        end_byte = data[1]

        user_lever_arm_x = data[2]
        user_lever_arm_y = data[3]
        user_lever_arm_z = data[4]

        rotation_rbvx = data[5]
        rotation_rbvy = data[6]
        rotation_rbvz = data[7]
        return start_byte, end_byte, user_lever_arm_x, user_lever_arm_y, user_lever_arm_z, \
            rotation_rbvx, rotation_rbvy, rotation_rbvz

    def reset_func(self, ser, size):
        '''
        send 'reset cmd' restore default parameters
        send 'get cmd'
        get the response msg by 'get cmd'
        '''
        read_size = ser.in_waiting
        data = ser.read(read_size)
        header_type = None
        packet_type = None 
        sniffer = True
        
        while sniffer is True:
            read_size = ser.in_waiting
            data = ser.read(read_size)
            reset_command = self.reset()
            ser.write(bytes(reset_command))
            get_command = self.get_params()[0]
            ser.write(bytes(get_command))
            for i, _ in enumerate(data):
                ser.write(bytes(get_command))
                lens = len(data)
                header_type = data[i:(i+2)].hex()
                if header_type == '5555' and \
                    lens - i > size:
                    packet_type = data[(i+2):(i+4)].hex()
                if packet_type == '6742' and \
                    lens - i > size:
                    latest = data[(i+4):(i+size-2)]
                    sniffer = False
                    break
        return latest

    def set_func(self, ser):
        '''
        send 'set cmd' to config the target parameter
        '''
        set_command = self.set_params(
            self.properties["initial"]["userParameters"])
        ser.write(bytes(set_command))

    def save_func(self, ser):
        '''
        send 'save cmd' save configuration parameter permanently 
        '''
        save_command = self.save_params()
        ser.write(bytes(save_command))

    def restart_func(self, ser):
        '''
        send 'restart cmd' to reconnect the device
        '''
        restart_command = self.restart()
        ser.write(bytes(restart_command))
        time.sleep(1)

    def repower_func(self):
        '''
        use GPIO from raspberry
        Power on the device after it is powered off
        '''
        GPIO.power_switch()
        time.sleep(2)

    def get_func(self, ser, size, compare_msg):
        '''
        send 'get cmd' 
        get the response msg and compare
        if compare passed record it 
        ''' 
        header_type = None
        packet_type = None 
        sniffer = True 
        while sniffer is True:
            read_size = ser.in_waiting
            data = ser.read(read_size)
            lens = len(data) 
            get_command = self.get_params()[0]
            ser.write(bytes(get_command))
            for i, _ in enumerate(data):
                lens = len(data)
                header_type = data[i:(i+2)].hex()
                if header_type == '5555' and \
                    lens - i > (size + 1):
                    packet_type = data[(i+2):(i+4)].hex()
                if packet_type == '6742' and \
                    lens - i > (size + 1):
                    latest = data[(i+4):(i+size-2)]
                    if latest != compare_msg:
                        self.success_times = self.success_times + 1
                        sniffer = False
                        break
        
    def reopen_port(self, ser, sec):
        ser.close()
        time.sleep(sec)
        ser.open()

    def set_params(self, params, *args):
        '''
        set parameters
        '''
        input_parameters = self.properties['userConfiguration']
        grouped_parameters = {}

        for parameter in params:
            exist_parameter = next(
                (x for x in input_parameters if x['paramId'] == parameter['paramId']), None)
            if exist_parameter:
                has_group = grouped_parameters.__contains__(
                    exist_parameter['category'])
                if not has_group:
                    grouped_parameters[exist_parameter['category']] = []

                current_group = grouped_parameters[exist_parameter['category']]

                current_group.append(
                    {'paramId': parameter['paramId'], 'value': parameter['value'], 'type': exist_parameter['type']})

        for group in grouped_parameters.values():
            message_bytes = []
            for parameter in group:
                message_bytes.extend(
                    self.encode_value('int8', parameter['paramId']))
                message_bytes.extend(
                    self.encode_value(parameter['type'], parameter['value']))
            command_line = self.build_packet(
                'uB', message_bytes)
        return command_line

    def save_params(self, *args):
        '''
        save parameters
        '''
        command_line = self.build_input_packet('sC')
        return command_line

    def get_params(self, *args):
        '''
        Get all parameters
        '''
        conf_parameters = self.properties['userConfiguration']
        conf_parameters_len = len(conf_parameters)-1
        step = 10
        st_command_line = None
        nd_command_line = None

        for i in range(2, conf_parameters_len, step):
            start_byte = i
            end_byte = i+step-1 if i+step < conf_parameters_len else conf_parameters_len
            command_line = self.build_packet('gB', [start_byte, end_byte])
            if i == 2:
                st_command_line = command_line
            else:
                nd_command_line = command_line            
        return st_command_line, nd_command_line
    
    def reset(self, *args):
        '''
        reset parameters to default
        '''
        command_line = self.build_input_packet('rD')
        return command_line

    def restart(self, *args):
        '''
        restart the device
        '''
        command_line = self.build_input_packet('SR')
        return command_line

    def unpack_payload(self, name, properties, param=False, value=False):
        '''
        unpack payload
        '''
        input_packet = next(
            (x for x in properties['userMessages']['inputPackets'] if x['name'] == name), None)
        if name == 'ma':
            input_action = next(
                (x for x in input_packet['inputPayload'] if x['actionName'] == param), None)
            return [input_action['actionID']]
        elif input_packet is not None:
            if input_packet['inputPayload']['type'] == 'paramId':
                return list(struct.unpack("4B", struct.pack("<L", param)))
            elif input_packet['inputPayload']['type'] == 'userParameter':
                payload = list(struct.unpack("4B", struct.pack("<L", param)))
                if properties['userConfiguration'][param]['type'] == 'uint64':
                    payload += list(struct.unpack("8B", struct.pack("<Q", value)))
                elif properties['userConfiguration'][param]['type'] == 'int64':
                    payload += list(struct.unpack("8B", struct.pack("<q", value)))
                elif properties['userConfiguration'][param]['type'] == 'double':
                    payload += list(struct.unpack("8B",
                                                struct.pack("<d", float(value))))
                elif properties['userConfiguration'][param]['type'] == 'uint32':
                    payload += list(struct.unpack("4B", struct.pack("<I", value)))
                elif properties['userConfiguration'][param]['type'] == 'int32':
                    payload += list(struct.unpack("4B", struct.pack("<i", value)))
                elif properties['userConfiguration'][param]['type'] == 'float':
                    payload += list(struct.unpack("4B", struct.pack("<f", value)))
                elif properties['userConfiguration'][param]['type'] == 'uint16':
                    payload += list(struct.unpack("2B", struct.pack("<H", value)))
                elif properties['userConfiguration'][param]['type'] == 'int16':
                    payload += list(struct.unpack("2B", struct.pack("<h", value)))
                elif properties['userConfiguration'][param]['type'] == 'uint8':
                    payload += list(struct.unpack("1B", struct.pack("<B", value)))
                elif properties['userConfiguration'][param]['type'] == 'int8':
                    payload += list(struct.unpack("1B", struct.pack("<b", value)))
                elif 'char' in properties['userConfiguration'][param]['type']:
                    c_len = int(properties['userConfiguration']
                                [param]['type'].replace('char', ''))
                    if isinstance(value, int):
                        length = len(str(value))
                        payload += list(struct.unpack('{0}B'.format(length),
                                                    bytearray(str(value), 'utf-8')))
                    else:
                        length = len(value)
                        payload += list(struct.unpack('{0}B'.format(length),
                                                    bytearray(value, 'utf-8')))
                    for i in range(c_len-length):
                        payload += [0x00]
                elif properties['userConfiguration'][param]['type'] == 'ip4':
                    ip_address = value.split('.')
                    ip_address_v4 = list(map(int, ip_address))
                    for i in range(4):
                        payload += list(struct.unpack("1B",
                                                    struct.pack("<B", ip_address_v4[i])))
                elif properties['userConfiguration'][param]['type'] == 'ip6':
                    ip_address = value.split('.')
                    payload += list(struct.unpack('6B',
                                                bytearray(ip_address, 'utf-8')))
                return payload

    def encode_value(self, data_type, data):
        '''
        the encode function
        '''
        payload = []
        if data_type == 'uint64':
            payload += list(struct.unpack("8B", struct.pack("<Q", data)))
        elif data_type == 'int64':
            payload += list(struct.unpack("8B", struct.pack("<q", data)))
        elif data_type == 'double':
            payload += list(struct.unpack("8B",
                                        struct.pack("<d", float(data))))
        elif data_type == 'uint32':
            payload += list(struct.unpack("4B", struct.pack("<I", data)))
        elif data_type == 'int32':
            payload += list(struct.unpack("4B", struct.pack("<i", data)))
        elif data_type == 'float':
            payload += list(struct.unpack("4B", struct.pack("<f", data)))
        elif data_type == 'uint16':
            payload += list(struct.unpack("2B", struct.pack("<H", data)))
        elif data_type == 'int16':
            payload += list(struct.unpack("2B", struct.pack("<h", data)))
        elif data_type == 'uint8':
            payload += list(struct.unpack("1B", struct.pack("<B", data)))
        elif data_type == 'int8':
            payload += list(struct.unpack("1B", struct.pack("<b", data)))
        elif 'char' in data_type:
            c_len = int(data_type.replace('char', ''))
            if isinstance(data, int):
                length = len(str(data))
                payload += list(struct.unpack('{0}B'.format(length),
                                            bytearray(str(data), 'utf-8')))
            else:
                length = len(data)
                payload += list(struct.unpack('{0}B'.format(length),
                                            bytearray(data, 'utf-8')))
            for i in range(c_len-length):
                payload += [0x00]
        elif data_type == 'ip4':
            ip_address = data.split('.')
            ip_address_v4 = list(map(int, ip_address))
            for i in range(4):
                payload += list(struct.unpack("1B",
                                            struct.pack("<B", ip_address_v4[i])))
        elif data_type == 'ip6':
            ip_address = data.split('.')
            payload += list(struct.unpack('6B',
                                        bytearray(ip_address, 'utf-8')))
        return payload

    def build_packet(self, message_type, message_bytes=[]):
        COMMAND_START = [0x55, 0x55]
        packet = []
        packet.extend(bytearray(message_type, 'utf-8'))

        msg_len = len(message_bytes)
        packet.append(msg_len)
        final_packet = packet + message_bytes

        CRC = self.calc_crc(final_packet)

        return COMMAND_START + final_packet + CRC

    def build_input_packet(self, name, properties=None, param=False, value=False):
        packet = []
        if not param and not value:
            packet = self.build_packet(name)
        else:
            payload = self.unpack_payload(name, properties, param, value)
            packet = self.build_packet(name, payload)
        return packet

    def calc_crc(self, payload):
        '''
        CRC
        '''
        crc = 0x1D0F
        for bytedata in payload:
            crc = crc ^ (bytedata << 8)
            i = 0
            while i < 8:
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc = crc << 1
                i += 1

        crc = crc & 0xffff
        crc_msb = (crc & 0xFF00) >> 8
        crc_lsb = (crc & 0x00FF)
        return [crc_msb, crc_lsb]

if __name__ == "__main__":
    path = os.getcwd()
    port = 'COM8'
    baud = 230400
    ser = serial.Serial(port, baud, timeout=0.1)
    logf = open(path + '/logger/test_report.txt', 'w+')

    unit = ConfigTest(ser, logf)

    logf.write('###Section 1 (Parameter configuration pressure test) is started###\n\r')
    unit.set_cmd_test()

    logf.write('\r\r###Section 2 (Check gN packet after reset) is started###\n\r')
    unit._restart()

    logf.write('\r\r###Section 3 (Coordinate system configuration test) is started###\n\r')
    unit.CSYS_config_test()


       
