from RTK330LA_Uart import UART_Dev
from Test_Cases import Test_Section
from Test_Cases import Test_Case
from RTK330LA_Tests import Test_Scripts
from RTK330LA_Tests import Test_Environment
#import scripts

def ping_message_test():
    print(" ")

def unit_baudrate_test():
    print("printing from function")

def continuous_packet_type_test():
    print("printing from function")

if __name__ == "__main__":

    uut = UART_Dev("COM3", 230400)
    #print(uut)
    print("\r\n \t#######   RTK330LA UART Interface Verification V1.0   #######\r\n")
    serial_number, model, version = uut.get_serial_number()

    print("\r\n \t# UUT Model: ", model)
    print("\r\n \t# UUT Serial Number: ", serial_number)
    print("\r\n \t# UUT Version: ", version)

    env = Test_Environment(uut)
    env.setup_tests()
    print("\r\n \t##########  Executing tests...   ##########################\r\n")
    env.run_tests()
    print("\r\n \t##########  Results   #####################################\r\n")
    env.print_results()

    file_name = 'test_results_' + str(serial_number) + '_' + str(version) + '.csv'
    env.log_results(file_name)
    
    uut.UART_close()
