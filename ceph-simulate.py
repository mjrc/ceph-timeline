#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#filename           : rados_simulator.py
#description        : Simulates usage patterns on a Ceph Storage Cluster
#                     for testing and/or Benchmarking purposes. The script
#                     uses the Librados library.  
#author             : Chris Kuipers
#email              : chris.kuipers@os.nl
#date               : 2018/03/19
#version            : 0.9
#usage              : $ python ceph_usage_simulator.py
#license            : MIT
#python_version     : 2.7.14
#==============================================================================

import argparse

# arguments
ap = argparse.ArgumentParser()
ap.add_argument("-p", "--pool", type=str, required=True,
        help="Ceph Pool to interact with")
ap.add_argument("--conf", type=str, required=False, default='/etc/ceph/ceph.conf',
        help="Specify the configuration file containing the monitor address. Defaults to /etc/ceph/ceph.conf")
ap.add_argument("--keyf", type=str, required=False, default='/etc/ceph/ceph.client.admin.keyring',
        help="Specify the keyfile to use. Defaults to /etc/ceph/ceph.client.admin.keyring")
ap.add_argument("-w", "--write", type=int, required=False, default=24,
        help="Enable or disable writes")
ap.add_argument("-m", "--modify", type=int, required=False, default=15,
        help="Enable or disable object modifications")
ap.add_argument("-r", "--read", type=int, required=False, default=12,
        help="Enable or disable object reads")
ap.add_argument("-d", "--delete", type=int, required=False, default=5,
        help="Enable or disable object deletions")
ap.add_argument("-s", "--sleep", type=int, required=False, default=1,
        help="Enable or disable the random sleep interval")
ap.add_argument("-c", "--count", type=int, required=False, default=10000,
        help="Number of operations to perform")
ap.add_argument("--hash", type=int, required=False, default=1, choices=[0,1],
        help="Enable or disable hash calculations")
ap.add_argument("-l", "--logging", type=int, required=False, default=1, choices=[0,1,2,3],
        help="Enable (1), disable (0) logging or Overwrite (2) the SQLite database. 3 also first deletes the testpool")
ap.add_argument("--dbpath", type=str, required=False, default='./rados-simulations.db',
        help="Enable or disable logging in SQLite database")
args = vars(ap.parse_args())

#print used settings
print("[SETTINGS]\n" + \
"        pool     : " + str(args["pool"]) + "\n" + \
"        conf     : " + str(args["conf"]) + "\n" + \
"        keyf     : " + str(args["keyf"]) + "\n" + \
"        writes   : " + str(args["write"]) + "\n" + \
"        modify   : " + str(args["modify"]) + "\n" + \
"        reads    : " + str(args["read"]) + "\n" + \
"        deletions: " + str(args["delete"]) + "\n" + \
"        # actions: " + str(args["count"]) + "\n" + \
"        hashing  : " + str(args["hash"]) + "\n" + \
"        logging  : " + str(args["logging"]) + "\n" + \
"        dbpath   : " + str(args["dbpath"]) + "\n")

import os
import rados 
import rbd 
import dataset
import json
import numpy as np
from hashlib import sha256
from time import time, sleep
import pprint

# Static variables
DATABASE_CONNECTION = 'sqlite:///'



def randomData():
        # Create random data using urandom
        return os.urandom(int(os.urandom(3).encode('hex'),16))
        #return int(os.urandom(3).encode('hex',16)

def objectName():
        # Create random object name
        return "sheep_" + os.urandom(6).encode('hex')

def waitTime():
        # Generate random timout interval
        return int(os.urandom(1).encode('hex'),16)
        #return int(os.urandom(3).encode('hex',16)

def nextAction():
        # Determine the next action to perform
        # Available options: wait, write, modify, read, delete
        # The probability of the operation depends upon the
        # probability as given by the argument. Default is 1

        # Create list to hold all possible operations
        operations = []
        probabilities = []

        if args["sleep"]:
                operations.append("wait")
                probabilities.append(args["sleep"])

        # Only add write to the list if applicable
        if args["write"]:
                operations.append("write")
                probabilities.append(args["write"])
        # Only add modify to the list if applicable
        if args["modify"]:
                operations.append("modify")
                probabilities.append(args["modify"])
        # Only add read to the list if applicable
        if args["read"]:
                operations.append("read")
                probabilities.append(args["read"])
        # Only add delete to the list if applicable
        if args["delete"]:
                operations.append("delete")
                probabilities.append(args["delete"])
        
        # Converting the arbitrairy probabilities to relative probabilities
        total = 0
        # Calculate total
        for n in probabilities:
                total += float(n)
        # Convert to relative
        for i, n in enumerate(probabilities):
                probabilities[i] = (float(n)/total)
        return np.random.choice(operations, 1, probabilities)[0]

# def randomObject(database):
#         # Return one, randomly picked, object which was previously created
#         r = db.find(order_by='object', _limit=10)
#         a = []
#         for i in r:
#                 a.append(i['object'])
#         return (np.random.choice(a,1)[0])

def randomObject():
        # Return one, randomly picked, object which was previously created.

        # Pick one based on the database
        #if args["logging"]:
        a = [] 
        if False:
                #r = database.query("SELECT DISTINCT object FROM "+database.table.fullname+" WHERE action <> delete LIMIT 10")
                r = database.query("SELECT DISTINCT object FROM 'rados-simulations-"+args['pool']+"' EXCEPT SELECT object FROM 'rados-simulations-"+args['pool']+"' WHERE action == 'delete'")

                while True :
                        try :
                                #i = r.next()
                                a.append(r.next()['object'])
                        except StopIteration :
                                break 
                # a = []
                # for i in r:
                #         a.append(i['object'])
        else:
                a = objectUniverse
        if not objectUniverse.__len__():
            return None
        return (np.random.choice(a,1)[0])

def main():

        # Cleaning up and preparation stuff
        if not os.path.isfile(args["conf"]):
                args["conf"] = './ceph.conf'

        if not os.path.isfile(args["keyf"]):
                args["keyf"] = './ceph.client.admin.keyring'

        # Connect to Ceph cluster and initiate cluster-object
        cluster = rados.Rados(conffile = args["conf"], conf = dict (keyring = args["keyf"]))

        print("\nCluster connection")
        print("==================")
        # Get Librados' version
        print("Librados version: " + str(cluster.version()))
        # Monitor we're going to connect to:
        print("Connecting to   : " + str(cluster.conf_get('mon initial members')))
        cluster.connect()
        print("Cluster ID      : " + cluster.get_fsid())

        print("Pool exists     : " + str(cluster.pool_exists(args['pool'])))
        if args["logging"] == 3:
                print("\n\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                print("!! DELETING POOL IN 5 SECONDS !!")
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                print("Quit while you can! Ctrl+C")
                sleep(5)
                cluster.delete_pool(args['pool'])
                print("Done. Proceeding with recreation")
        # If logging is enabled, create or overwrite database and table
        #if args["logging"]:
        if True:
                if (args["logging"] == 2) or (args["logging"] == 3):
                        if os.path.isfile(args["dbpath"]):
                                os.remove(args["dbpath"])
                global database
                database = dataset.connect(DATABASE_CONNECTION + args["dbpath"])
                # db = database.create_table('ceph_simulations_'+args["pool"], primary_id=False)
                db = database.create_table('rados-simulations-'+args["pool"])
                
        if not cluster.pool_exists(args['pool']):
                cluster.create_pool(args['pool'])
                print("\nCreating pool...")
        # Creating the I/O context so we can interact with objects
        print("\nInitiating a I/O context")
        print("------------------------")
        # Declaring the I/O context as global variable so we can access it everywhere
        global ioctx                
        ioctx = cluster.open_ioctx(args["pool"])

        # Looping the operations:
        print("\nLooping through all actions")
        print("===========================")
        print("Total operations: " + str(args["count"]))

        i = 0
        global objectUniverse
        objectUniverse = []
        nextActionWrite = True
        while i < args["count"]:
                i += 1
                action = nextAction()
                if nextActionWrite and args["write"]:
                        action = "write"

                if action == "wait":
                        sec = waitTime()*0.1*0.2
                        print("\nWaiting "+str(sec)+" seconds")
                        sleep(sec)
                        #sleep(1)
                if action == "write":
                        print("\nWriting objects")
                        print("---------------")
                        print("Iteration: "+str(i)+"/"+str(args["count"]))
                        name = objectName()
                        data = randomData()
                        print("Writing  : "+ str(name))
                        print("Size     : "+ str(data.__sizeof__()/1024/1024) + "MB")
                        
                        before = time()
                        ioctx.write_full(name,data)
                        now = time()
                        diff = now - before
                        
                        hash = sha256(data).hexdigest()
                        print("SHA256   : " + hash)
                        print("Time     : " + str(now))
                        print("Diff     : "+ str(diff*100))

                        objectUniverse.append(name)
                        nextActionWrite = False

                        if args["logging"]:
                                db.insert(dict( object=name, 
                                                action=action, 
                                                size=data.__sizeof__(),
                                                sha256=hash,
                                                time=str(now),
                                                timedelta=str(diff)))
                if action == "modify":
                        print("\nModifying objects")
                        print("-----------------")
                        print("Iteration: "+str(i)+"/"+str(args["count"]))
                        name = randomObject()
                        data = randomData()
                        print("Modding  : "+ str(name))
                        print("Size     : "+ str(data.__sizeof__()/1024/1024) + "MB")
                        
                        before = time()
                        ioctx.write_full(name,data)
                        now = time()
                        diff = now - before
                        
                        hash = sha256(data).hexdigest()
                        print("SHA256   : " + hash)
                        print("Time     : " + str(now))
                        print("Diff     : "+ str(diff*100))

                        if args["logging"]:
                                db.insert(dict( object=name, 
                                                action=action, 
                                                size=data.__sizeof__(),
                                                sha256=hash,
                                                time=str(now),
                                                timedelta=str(diff)))                       
                if action == "read":
                        print("\nReading objects")
                        print("---------------")
                        print("Iteration: "+str(i)+"/"+str(args["count"]))
                        name = randomObject()
                        print("Reading  : "+ str(name))
                        before = time()
                        data = ioctx.read(name)
                        now = time()
                        diff = now - before
                        
                        print("Size     : "+ str(data.__sizeof__()/1024/1024) + "MB")

                        hash = sha256(data).hexdigest()
                        print("SHA256   : " + hash)
                        print("Time     : " + str(now))
                        print("Diff     : " + str(diff*100))

                        if args["logging"]:
                                db.insert(dict( object=name, 
                                                action=action, 
                                                size=data.__sizeof__(),
                                                sha256=hash,
                                                time=str(now),
                                                timedelta=str(diff)))                      
                if action == "delete":
                        print("\nDeleting objects")
                        print("----------------")
                        print("Iteration: "+str(i)+"/"+str(args["count"]))
                        name = randomObject()
                        print("Deleting : "+ str(name))
                        if not name:
                            print("COULD NOT DELETE: NO OBJECTS LEFT!!!")
                            db.insert(dict( action="COULD NOT DELETE", time=str(time())))
                            nextActionWrite = True
                        else:
                            before = time()
                            try:
                                    ioctx.remove_object(name)
                            except:
                                    raise
                        
                            now = time()
                            diff = now - before
                        
                            print("Time     : " + str(now))
                            print("Diff     : " + str(diff*100))

                            objectUniverse.remove(name)
                            if not objectUniverse.__len__():
                                nextActionWrite = True

                            if args["logging"]:
                                    db.insert(dict( object=name,
                                                    action=action,
                                                    time=str(now),
                                                    timedelta=str(diff)))

def cleanup():
        print ("\nClosing the connection.")
        ioctx.close()
        print("\n“I’m too old for this.”")
        print("  --Lethal Weapon")

if __name__ == "__main__":
        try:
                main()
        except KeyboardInterrupt:
                print("\n\nCtrl+C catched")
                pass
        finally:
                cleanup()
