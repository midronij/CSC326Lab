import boto3
import boto.ec2
import os

def terminate(elastic_IP):
    global allocation_id

    ec2 = boto3.client('ec2')
    conn = boto.ec2.connect_to_region("us-east-1")
    
    filters = {"ip-address": elastic_IP}
    instances = conn.get_only_instances(filters=filters)

    filters = [{'Name': 'public-ip', 'Values': [elastic_IP]}]

    addresses = ec2.describe_addresses(Filters=filters)

    inst_id = str(instances[0].id)
    alloc_id = addresses['Addresses'][0]['AllocationId']
    
    ec2.release_address(AllocationId=alloc_id)
    conn.terminate_instances(instance_ids=[inst_id,])

if __name__ == "__main__":
    elastic_IP = raw_input("Enter the public IP address of the instance to terminate:\n")

    #terminate the instance and release the elastic IP
    try:
        terminate(elastic_IP)
    except:
        print "Instance termination failed. Please email jackie.midroni@mail.utoronto.ca ASAP so that she can make sure she doesn't get charged by Amazon."
    else:
        print "Successfully terminated"
