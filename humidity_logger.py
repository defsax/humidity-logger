import glob
import serial
import time
from datetime import datetime
from multiprocessing import Process

t = datetime.now()
start_time = t.strftime("%m-%d-%Y_%H-%M-%S")

def list_serial_devices():
    ports = glob.glob('/dev/ttyACM[0-9]*')
    res = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            res.append(port)
        except:
            pass
    return res


def log_data(temp, rh, device, loc):
    # log temp and rh for each sensor          

    if temp == 'nan' or rh == 'nan':
        print("not logging:", temp, rh)
        return
        
    if float(temp) < 0 or float(rh) < 0:
        print("not logging:", temp, rh)
        return
    
    # ~ print("logging:", temp, rh, device)
    
    try:
        now = datetime.now()
        date_time = now.strftime("%m-%d-%Y_%H-%M-%S")
        with open(loc, "a") as f:
            f.write(date_time + ',' + rh + ',' + temp + ',' + device +'\n')
            f.close()
    except:
        print("error")

def average_samples(samples):
    avg_temp = 0
    avg_humd = 0
    
    for sample in samples:
        rh = sample.split(',')[0]
        temp = sample.split(',')[1]
        
        avg_temp += float(temp)
        avg_humd += float(rh)
        
    avg_temp = avg_temp / len(samples)
    avg_humd = avg_humd / len(samples)
    # ~ print('avg_t:', avg_temp)
    # ~ print('avg_rh:', avg_humd)
    
    return str(round(avg_temp, 2)), str(round(avg_humd, 2))

def log_thread(port, short_loc, long_loc):
    samples = []
    while True:
        # ~ print(port.in_waiting)
        if port.in_waiting > 0:
            port.reset_input_buffer()
        line = port.readline()
        if not line:
            break
        
        line = line.decode('utf-8')
        line = line.rstrip()
        
        samples.append(line)
        # ~ print('samples length:',len(samples))
        # ~ print('samples:', samples)
        
        # length of samples should correlate to number of minutes
        if len(samples) == 10:
            avg_temp, avg_humd = average_samples(samples)
            device = line.split(',')[2]
            log_data(avg_temp, avg_humd, device, long_loc)
            samples = []
            
        rh = line.split(',')[0]
        temp = line.split(',')[1]
        device = line.split(',')[2]
        log_data(temp, rh, device, short_loc)
        
        
# wait for sensors to start?
time.sleep(60)
device_list = list_serial_devices()

print(device_list)

if getattr(device_list, 'size', len(device_list)):  
    # set up data file only if there's a sensor connected
    try:
      short_sample_loc = "./data/data_short_"+start_time+".txt"
      with open(short_sample_loc, "a") as f:
        f.write("time,humidity,temperature,sensor_id\n")
        f.close()
      
      long_sample_loc = "./data/data_long_"+start_time+".txt"
      with open(long_sample_loc, "a") as f:
        f.write("time,humidity,temperature,sensor_id\n")
        f.close()
    except:
      print("write setup error")
    
    for device in device_list:
        print('device:',device)
        port = serial.Serial(device, 9600)
        p = Process(target=log_thread, args=(port,short_sample_loc, long_sample_loc,))
        p.start()
        # ~ p.join()
else: 
    print("No arduino(s) connected")
