import boto3
import boto.ec2
import os
import time
from crawler import crawler

def run():
    ec2 = boto3.client('ec2')

    conn = boto.ec2.connect_to_region("us-east-1")

    os.system("rm key.pem")

    key_pair = conn.create_key_pair("key")
    key_pair.save("")

    group = conn.create_security_group("csc326-group23", "insert description here")
    group.authorize("icmp", -1, -1, "0.0.0.0/0")
    group.authorize("tcp", 22, 22, "0.0.0.0/0")
    group.authorize("tcp", 80, 80, "0.0.0.0/0")

    resp = conn.run_instances("ami-8caa1ce4", instance_type="t1.micro", key_name="key", security_groups=["csc326-group23"])
    inst = resp.instances[0]
    inst_id = str(inst.id)

    while inst.update() != "running": #wait until the instance is actually running
        time.sleep(5)

    elastic_IP = conn.allocate_address()
    elastic_IP.associate(inst_id)

    return (str(elastic_IP)).replace("Address:", "")

def deploy(elastic_IP):
    #copy over files
    os.system("scp -o StrictHostKeyChecking=no -i key.pem CSC326Project.tar.gz ubuntu@" + elastic_IP + ":~/")
    os.system("scp -o StrictHostKeyChecking=no -i key.pem pythonsqlite.db ubuntu@" + elastic_IP + ":~/")
    #os.system("ssh -i key.pem ubuntu@" + elastic_IP) #access instance

    os.system("ssh -o StrictHostKeyChecking=no -i key.pem ubuntu@" + elastic_IP + " tar xvzf CSC326Project.tar.gz")
    os.system("ssh -o StrictHostKeyChecking=no -i key.pem ubuntu@" + elastic_IP + " cp pythonsqlite.db CSC326Project")
    os.system("ssh -o StrictHostKeyChecking=no -i key.pem ubuntu@" + elastic_IP + " cd CSC326Project")
    os.system("ssh -o StrictHostKeyChecking=no -i key.pem ubuntu@" + elastic_IP + " sudo apt-get update -y")
    os.system("ssh -o StrictHostKeyChecking=no -i key.pem ubuntu@" + elastic_IP + " sudo apt-get install python-pip -y")

    #install python packages needed
    os.system("ssh -o StrictHostKeyChecking=no -i key.pem ubuntu@" + elastic_IP + " sudo pip install bottle")
    os.system("ssh -o StrictHostKeyChecking=no -i key.pem ubuntu@" + elastic_IP + " sudo pip install google-api-python-client")
    os.system("ssh -o StrictHostKeyChecking=no -i key.pem ubuntu@" + elastic_IP + " sudo pip install oauth2client")
    os.system("ssh -o StrictHostKeyChecking=no -i key.pem ubuntu@" + elastic_IP + " sudo pip install credentials")
    os.system("ssh -o StrictHostKeyChecking=no -i key.pem ubuntu@" + elastic_IP + " sudo pip install beaker")
    os.system("ssh -o StrictHostKeyChecking=no -i key.pem ubuntu@" + elastic_IP + " sudo pip install pygtrie")

    #start tmux session and run website
    os.system("ssh -o StrictHostKeyChecking=no -i key.pem ubuntu@" + elastic_IP + " -t tmux new-session -d -s s0")
    os.system("ssh -o StrictHostKeyChecking=no -i key.pem ubuntu@" + elastic_IP + " -t tmux detach -s s0")
    os.system("ssh -o StrictHostKeyChecking=no -i key.pem ubuntu@" + elastic_IP + " -t tmux send -t s0 cd SPACE CSC326Project ENTER")
    os.system("ssh -o StrictHostKeyChecking=no -i key.pem ubuntu@" + elastic_IP + " -t tmux send -t s0 sudo SPACE python SPACE WebpageRemote.py ENTER")

if __name__ == "__main__":

    #get website info
    #bot = crawler(None, "urls.txt")
    #bot.crawl(depth=1)

    #create AWS instance
    elastic_IP = run()

    #copy over files and deploy website
    #deploy(elastic_IP)

    print "Access the search engine via: " + str(elastic_IP)
    
 
    
