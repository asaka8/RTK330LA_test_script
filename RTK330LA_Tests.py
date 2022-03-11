import time
import struct
import io
import pip
from RTK330LA_Ethernet import Ethernet_Dev
from Test_Logger import TestLogger
from Test_Cases import Test_Section
from Test_Cases import Test_Case
from Test_Cases import Code
from Test_Cases import Condition_Check


INPUT_PACKETS = [b'\x02\x0b']
OTHER_OUTPUT_PACKETS = [b'\x01\n', b'\x06\n', b'\x07\n', b'\x08\n']

user_parameters = [0, 0, 0, 0, 0,  0, 0, 0, 0, 0, 0, 0]
rtcm_data = [1, 2, 3, 4, 5, 6, 7, 8]
vehicle_speed_value = 80
LONGTERM_RUNNING_COUNT = 1000000

output_time = []


# Add test scripts here
class Test_Scripts:
    uut = None

    def __init__(self, device):
        Test_Scripts.uut = device
    
    def hex_string(self, number_bytes = []):
        if number_bytes is None:
            return None
        return hex(int(struct.unpack('<H', number_bytes)[0]))
  
    def set_base_rtcm_data(self):
        command = INPUT_PACKETS[0]
        message_bytes = []
        
        message_bytes.extend(rtcm_data)
        
        for i in range(10):
            self.uut.send_message(command, message_bytes)
            time.sleep(0.2)
        
        return True, self.hex_string(command), self.hex_string(command)
        
    def set_vehicle_speed_data(self):
        command = INPUT_PACKETS[4]
        message_bytes = []        

        field_value_bytes = struct.pack('<f', vehicle_speed_value)
        message_bytes.extend(field_value_bytes)
        
        self.uut.send_message(command, message_bytes)
        
        return True, self.hex_string(command), self.hex_string(command)
           
    def output_packet_callback(self, packet):
        output_time.append(time.time())
        pass
        
    def output_packet_raw_imu_data_test(self):
        global output_time     
        result = True
        command = OTHER_OUTPUT_PACKETS[0]
        
        cmd_type = struct.unpack('>H', command)[0]
        for i in range(10):
            output_time = []
            self.uut.read(2, cmd_type, self.output_packet_callback, 2)
            if(len(output_time) == 2):
                output_time_internal = output_time[1] - output_time[0]
                if(output_time_internal > 0.019):  #100Hz
                    print(output_time_internal)
                    result = False
                    break
            else:
                result = False
                break         
        
        if(result):
            return True, self.hex_string(command), self.hex_string(command)
        else:
            return False, self.hex_string(command), self.hex_string(command)

    def output_rtcm_data_test(self):
        global output_time 
        
        result = True
        command = OTHER_OUTPUT_PACKETS[1]
        
        cmd_type = struct.unpack('>H', command)[0]
        for i in range(10):
            output_time = []
            self.uut.read(2, cmd_type, self.output_packet_callback, 2)
            if(len(output_time) == 2):
                output_time_internal = output_time[1] - output_time[0]
                if(output_time_internal > 0.059):
                    print(output_time_internal)
                    result = False
                    break
            else:
                result = False
                break      
        
        if(result):
            return True, self.hex_string(command), self.hex_string(command)
        else:
            return False, self.hex_string(command), self.hex_string(command)
            
    def output_corrIMU_test(self):
        global output_time 
        
        result = True
        command = OTHER_OUTPUT_PACKETS[2]
        
        cmd_type = struct.unpack('>H', command)[0]
        for i in range(10):
            output_time = []
            self.uut.read(2, cmd_type, self.output_packet_callback, 2)
            if(len(output_time) == 2):
                output_time_internal = output_time[1] - output_time[0]
                if(output_time_internal > 0.035):   # 50HZ
                    print(output_time_internal)
                    result = False
                    break
            else:
                result = False
                break             
        
        if(result):
            return True, self.hex_string(command), self.hex_string(command)
        else:
            return False, self.hex_string(command), self.hex_string(command)  

    def output_rtcm_sta_spp_test(self):
        global output_time 
        
        result = True
        command = OTHER_OUTPUT_PACKETS[3]
        
        cmd_type = struct.unpack('>H', command)[0]
        for i in range(10):
            output_time = []
            self.uut.read(2, cmd_type, self.output_packet_callback, 3)
            if(len(output_time) == 2):
                output_time_internal = output_time[1] - output_time[0]
                if(output_time_internal > 0.15):
                    print(output_time_internal)
                    result = False
                    break
            else:
                result = False
                break      
        
        if(result):
            return True, self.hex_string(command), self.hex_string(command)
        else:
            return False, self.hex_string(command), self.hex_string(command)  


#################################################

class Test_Environment:

    def __init__(self, device):
        self.scripts = Test_Scripts(device)
        self.test_sections = []

    # Add test scetions & test scripts here
    def setup_tests(self):

        section1 = Test_Section("ETHERNET Transaction Verification")
        self.test_sections.append(section1)
        section1.add_test_case(Code("set base rtcm data test",  self.scripts.set_base_rtcm_data))

        section2 = Test_Section("Output Packet Test")
        self.test_sections.append(section2)
        section2.add_test_case(Code("raw imu data test", self.scripts.output_packet_raw_imu_data_test))
        section2.add_test_case(Code("rtcm data test", self.scripts.output_rtcm_data_test))
        section2.add_test_case(Code("corrIMU test", self.scripts.output_corrIMU_test))
        section2.add_test_case(Code("rtcm sta spp test", self.scripts.output_rtcm_sta_spp_test))

       
    def run_tests(self):
        for section in self.test_sections:
            section.run_test_section()

    def print_results(self):
        print("Test Results:")
        for section in self.test_sections:
            print("Section " + str(section.section_id) + ": " + section.section_name + "\r\n")
            for test in section.test_cases:
                id = str(section.section_id) + "." + str(test.test_id)
                result_str = "Passed --> " if test.result['status'] else "Failed --x "
                print(result_str + id + " " + test.test_case_name + " Expected: "+ test.result['expected'] + " Actual: "+  test.result['actual'] + "\r\n")

    def _create_csv(self, file_name, fieldnames):
        with open(file_name, 'w+') as out_file:
            writer = csv.DictWriter(out_file, fieldnames = fieldnames)
            writer.writeheader()

    def log_results(self, file_name):
        logger = TestLogger(file_name)
        field_names = ['id', 'test_name', 'expected', 'actual', 'status']
        logger.create(field_names)
        for section in self.test_sections:
            for test in section.test_cases:
                logger.write_log(test.result)
