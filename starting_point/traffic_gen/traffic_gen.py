import sys, subprocess, time


def main():
    setup()
    param = sys.argv
    traffic(param[1],param[2],param[3])
    print("Traffic generation completed.")
    return

def traffic(duration, bandwidth, packet_size, busy_wait=True):
    """
    duration in seconds
    bandwidth in Gbps
    packet_size in bytes
    """

    if float(bandwidth) >= 2.5:
        runner = 'RDMA'
    else:
        runner = 'iperf3'

    if bandwidth == 0:
        if busy_wait:
            start = time.time()
            while time.time() - start < duration:
                pass
        else:
            time.sleep(duration)
            
    elif runner=='RDMA':

        print('Generating RDMA traffic with ib_send_bw...')

        # result1 = subprocess.Popen(f'sudo ip netns exec ns1 ib_read_bw -d mlx5_0 -b -D {duration} --cpu_util --report_gbits --rate_limit={bandwidth} --typical_pkt_size={packet_size} --rate_limit_type=PP', shell=True, stdout=subprocess.PIPE)
        # time.sleep(1)
        # result2 = subprocess.Popen(f'sudo ip netns exec ns2 ib_read_bw -d mlx5_1 -b -D {duration} --cpu_util --report_gbits --rate_limit={bandwidth} --typical_pkt_size={packet_size} --rate_limit_type=PP 192.168.1.1', shell=True, stdout=subprocess.PIPE)
        # result1 = subprocess.Popen(f'sudo ip netns exec ns1 ib_read_bw -d mlx5_0 -D {duration} --cpu_util --report_gbits --rate_limit={bandwidth} --mtu={packet_size} -F', shell=True, stdout=subprocess.PIPE)
        # time.sleep(1)
        # result2 = subprocess.Popen(f'sudo ip netns exec ns2 ib_read_bw -d mlx5_1 -D {duration} --cpu_util --report_gbits --rate_limit={bandwidth} --mtu={packet_size} -F 192.168.1.1', shell=True, stdout=subprocess.PIPE)

        result1 = subprocess.Popen(f'sudo ip netns exec ns1 ib_send_bw -d mlx5_0 -D {duration} --cpu_util --report_gbits --rate_limit={bandwidth} --mtu={packet_size} -F', shell=True, stdout=subprocess.PIPE)
        time.sleep(1)
        result2 = subprocess.Popen(f'sudo ip netns exec ns2 ib_send_bw -d mlx5_1 -D {duration} --cpu_util --report_gbits --rate_limit={bandwidth} --mtu={packet_size} -F 192.168.1.1 --out_json', shell=True, stdout=subprocess.PIPE)

        # result1.wait()
        # result2.wait()

        print(result1.communicate()[0].decode("utf-8"))
        print("\n \n")
        print(result2.communicate()[0].decode("utf-8"))

        post_process = subprocess.Popen(f'sudo chmod 666 ~/workspace/network-profiling/power-modeling/automation/perftest_out.json', shell=True, stdout=subprocess.PIPE)
        post_process.wait()

    elif runner=='iperf3':
        
        print('Generating UDP traffic with iperf3...')
        
        clean_process = subprocess.Popen(f'rm -f ~/workspace/network-profiling/power-modeling/automation/perftest_out.json', shell=True, stdout=subprocess.PIPE)
        clean_process.wait()
    
        result1 = subprocess.Popen(f'sudo ip netns exec ns1 iperf3 -s -D -B 192.168.1.1', shell=True, stdout=subprocess.PIPE)
        time.sleep(1)
        result2 = subprocess.Popen(f'sudo ip netns exec ns2 iperf3 -u -B 192.168.1.2 -c 192.168.1.1 -b -J {bandwidth}G -l {packet_size} -t {duration} --logfile perftest_out.json', shell=True, stdout=subprocess.PIPE)
        
        time.sleep(int(duration))
        subprocess.Popen(f'sudo ip netns exec ns1 pkill -HUP iperf3', shell=True, stdout=subprocess.PIPE)
        
        post_process = subprocess.Popen(f'sudo chmod 666 ~/workspace/network-profiling/power-modeling/automation/perftest_out.json', shell=True, stdout=subprocess.PIPE)
        post_process.wait()
        
        
        

def setup():
    result = subprocess.run("sudo modprobe cpufreq_userspace",shell=True,capture_output=True, text=True)
    print(result.stdout)

    result = subprocess.run("sudo cpupower frequency-set --governor usermode",shell=True,capture_output=True, text=True)
    #print(result.stdout)

    result = subprocess.run("sudo cpupower frequency-set --freq 2400MHz",shell=True,capture_output=True, text=True)
    print(result.stdout)
    print("fix cpu performance")




if __name__ == "__main__":
    main()

