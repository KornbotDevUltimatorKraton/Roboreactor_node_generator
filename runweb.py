from flask import Flask,jsonify,request,render_template,redirect,url_for 
import os 
import getpass 
import configparser
import json 
import time 
import threading
import subprocess
import requests # Getting the request from the json api of the update version on the microcontroller support version path 
user = getpass.getuser() 
Home_path = '/home/'+str(user)+"/" #Home path to get the config file and project setting outside the node generator

Path = '/home/'+str(user)+"/Roboreactor_projects" # getting the file path 
Path_local = '/home/'+str(user)+"/Roboreactor_Gen_config"  # Generate the main path for config gen and code generator

path_serial = "/sys/class/tty"
mem_dir_create = [] 
app = Flask(__name__) 
serial_count = []


                      
                    
def host_info_callback(path_serial):
       
       list_serial = os.listdir(path_serial)
       for l in range(0,len(list_serial)):
          
           if len(list_serial[l].split("ttyACM")) >1: 
              
              if list_serial[l] not in serial_count: 
                  serial_count.append(list_serial[l])      
           if len(list_serial[l].split("ttyUSB")) >1: 
               if list_serial[l] not in serial_count:
                     serial_count.append(list_serial[l])
       for check_serial in serial_count: 
                       if check_serial not in list_serial: 
                                      serial_count.remove(check_serial) #remove the list of the serial in case not found attach on physical devices connection           

@app.route("/",methods=['GET','POST'])  # Initial page start will collect and send the local machine data to update into the front end local machine data
def index():
      
      return render_template("index.html")
      
@app.route('/filepath',methods=['GET','POST'])
def filepathcreate():
      if request.method == 'POST':
            print('Creating path....')
            print(request.get_json())  # parse as JSON
            code_json = request.get_json()
            print("Creating to this path",code_json.get('path'))
            try: 
                 print("Creating directory path")
                 
                 try:
                     config = configparser.ConfigParser()
                     config.add_section('Project_path')
                     print("Start writing config file......")
                     config.set('Project_path','path',code_json.get('path')) 
                     configfile = open(Path+"/config_project_path.cfg",'w') 
                     config.write(configfile) 
                 except: 
                     print("Start writing config file...")
                 os.mkdir(code_json.get('path'),mode=0o777)    
                
            except:
                print("Directory was created")
                message_status = {'dir_status':'created'}
                mem_dir_create.append(message_status)
                if len(mem_dir_create) >1: 
                     mem_dir_create.remove(mem_dir_create[0])
                print(mem_dir_create)
                 

            print(type(code_json)) 
            return 'OK created path', 200 
      else:
        try:
             config = configparser.ConfigParser()    
             config.read(Path+'/config_project_path.cfg') 
             list_data = os.listdir(Path)
             print(list_data)
             path_config = config['Project_path']['path']
             host_info_callback(path_serial)
             message = {'Local_machine_data':{'local_directory':path_config},'Serial_local':serial_count,'Directory_status':{'dir_status':'created'}}  # Getting the data from local machine by running the usb check loop and other local data components conection 
             return jsonify(message)  # serialize and use JSON headers
        except:
             print("Error in reading the config file")
@app.route('/code', methods=['GET', 'POST'])
def hello():

    # POST request
    if request.method == 'POST':
        print('Incoming..')
        print(request.get_json())  # parse as JSON
        code_json = request.get_json()
        print(type(code_json)) 
        #Start generating the file here 
        json_object = json.dumps(code_json) # getting the json config 
        Generated_node = open(Path+"/"+"node_generated.json", "w") 
        Generated_node.write(json_object) 
        Generated_node = open(Path+"/"+"node_generated.json", "r") 
        data = json.loads(Generated_node.read())
        print("Node of the code",data)
        os.system("python3 roboreactor_config_gen.py")
        return 'OK', 200
@app.route('/start_project', methods=['GET', 'POST'])
def start_project():

    # POST request
    if request.method == 'POST':
        print('Incoming..')
        print(request.get_json())  # parse as JSON
        code_json = request.get_json()
        print(type(code_json)) 
        #Start generating the file here 
        json_object = json.dumps(code_json) # getting the json config 
        print(json_object) 
        load_json = json.loads(json_object) 
        try:
            local_path = load_json.get('Local_machine_data').get('Local_machine_data').get('local_directory')
            print(local_path) #getting the test path directory 
        except: 
            print("local path blank please fill directory path") 
        #Generate the path on the supervisor to start software at boot 
        
        path_supervisor = "/lib/systemd/system/"  # Running the path for the software  on supervisor
        project_name = local_path.split('/')[len(local_path.split('/'))-1]
        log_project_path = "/var/log/"+str(project_name)
        command = "/usr/bin/python3 "
        try:
            os.mkdir(log_project_path,mode=0o777) # Crating the log project file 
        except:
             print("Directory was created")
        config = configparser.ConfigParser()
        config = configparser.RawConfigParser()
        config.optionxform = str
        sections = 'Unit' # Getting the project name 
        services = 'Service'
        wanted = 'Install'
        print(sections) 
        config.add_section(sections)
        config.set(sections,'Description','Project:'+str(project_name))
        config.set(sections,'After','multi-user.target')
        config.add_section(services)
        config.set(services,'Type','idle')
        config.set(services,'ExecStart',command+str(local_path)+"/"+str(project_name)+".py")
        config.add_section(wanted)
        config.set(wanted,'WantedBy','multi-user.target')
        configfile = open(path_supervisor+str(project_name)+".service",'w')
        config.write(configfile) 
        #os.system("sudo chmod 644 /lib/systemd/system/"+str(project_name)+".service") # Run the
     
       

        return 'OK', 200
@app.route('/restart_project', methods=['GET', 'POST'])
def restart_project():

    # POST request
    if request.method == 'POST':
        print('Incoming..')
        print(request.get_json())  # parse as JSON
        code_json = request.get_json()
        print(type(code_json)) 
        #Start generating the file here 
        json_object = json.dumps(code_json) # getting the json config 
        print(json_object) 
        load_json = json.loads(json_object)
        local_path = load_json.get('Local_machine_data').get('Local_machine_data').get('local_directory')
        print(local_path) #getting the test path directory 
        #Generate the path on the supervisor to start software at boot 
        
        path_supervisor = "/lib/systemd/system/"  # Running the path for the software  on supervisor
        project_name = local_path.split('/')[len(local_path.split('/'))-1]
        log_project_path = "/var/log/"+str(project_name)
        command = "/usr/bin/python3 "
        os.system("systemctl daemon-reload")
        os.system("systemctl enable "+str(project_name)+".service") 
        os.system("systemctl start "+str(project_name)+".service")
        return 'OK', 200
@app.route('/stop_project', methods=['GET','POST'])
def stop_project():
    # POST request
    if request.method == 'POST':
        print('Incoming..')
        print(request.get_json())  # parse as JSON
        code_json = request.get_json()
        print(type(code_json)) 
        #Start generating the file here 
        json_object = json.dumps(code_json) # getting the json config 
        print(json_object) 
        load_json = json.loads(json_object)
        local_path = load_json.get('Local_machine_data').get('Local_machine_data').get('local_directory')
        print(local_path) #getting the test path directory 
        #Generate the path on the supervisor to start software at boot 
        
        path_supervisor = "/lib/systemd/system/"  # Running the path for the software  on supervisor
        project_name = local_path.split('/')[len(local_path.split('/'))-1]
        log_project_path = "/var/log/"+str(project_name)
        command = "/usr/bin/python3 "
        os.system("systemctl stop "+str(project_name)+".service")
        return 'OK', 200   
    # GET request
    #else:
    #    message = {'greeting':'Hello from Flask!'}
    #    return jsonify(message)  # serialize and use JSON headers

#if __name__ =="__main__":
app.run(debug=True,threaded=True,host="0.0.0.0",port=8000)


