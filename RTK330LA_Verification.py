from RTK330LA_Ethernet import Ethernet_Dev
from Test_Cases import Test_Section
from Test_Cases import Test_Case
from RTK330LA_Tests import Test_Scripts
from RTK330LA_Tests import Test_Environment
#import scripts

def main():
    uut = Ethernet_Dev()
    print("\n#######   INS401 ETHERNET Interface Verification V1.0   #######\n")
    
    env = Test_Environment(uut)
    env.setup_tests()
    print("###########  Executing tests...   ##########################\n")
    env.run_tests()
    print("##########  Results   #####################################\n")
    env.print_results()

    file_name = 'test_results' + '.csv'
    env.log_results(file_name)


if __name__ == "__main__":
    
    main()