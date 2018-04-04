# Ceph Timeline Utility 

A forensic timeline utility for the Ceph Object Store. This utility is the product of the research peformed by Chris Kuipers and Mick Cox, for the Computer Crime & Forensics Course, System & Network Engineering, University of Amsterdam.  

<p align="center">
  <img width="250" src="https://raw.githubusercontent.com/mjrc/ceph-timeline/master/images/sne.png">
  <div style="padding: 35px;"></div>
  <img width="250" src="https://raw.githubusercontent.com/mjrc/ceph-timeline/master/images/ceph.png">
</p>


## Introduction ## 

Ceph is a distributed objec storage system developed for horizontal scaling and without invoking any single points of failure or major bottlenecks. These objects are subdivided by means of pools, placement groups and object storage devices (OSDs), and as such, are highly distributed. Next to that, objects can for a large degree be regarded as unstructured data which can grow into peta or exabytes in size. Furthermore, by the nature of Ceph, there is no central point of contact or broker, and as such, there is no central object allocation table. These elements make for a challenge to any forensic investigator meaning to investigate the cluster. 

Applying triage to such a large, unorganized corpus of storage would be a necessary step. To this end, we have created this timeline utility which can be used to investiage and apply triage in a live forensics investigation a Ceph system.

[View the interface](https://mjrc.github.io/ceph-timeline/)

## Documentation ## 

The repository includes the following: 
 - ceph-extract.py: a script which extracts object and cluster metadata
 - ceph-simulate.py: a script which fills a cluster in a random manner
 - index.html: a dashboard in DC.js for vizualizing a ceph cluster
 - data.json: example dataset, consumed by index.html
 - data-jsonify: a script to convert the 'ceph-objects' sqllite db
 - data-random-epoch.py: a script for randomizing epoch timestamps in data.json 


### Configuration  ### 
Before extraction script relies on a configuration and keyring file in order to communicate with a Ceph clusters. These are currently hard coded to be './ceph.conf' and './ceph.client.admin.keyring', and are expected to have a format such as below.


#### ceph.conf ####
```
[global]
fsid = a2bad4b9-f50c-46df-987a-cc6d2a2db114
mon_initial_members = ceph1
mon_host = <insert_ip_address_here>
auth_cluster_required = cephx
auth_service_required = cephx
auth_client_required = cephx

[mon]
mon_allow_pool_delete = true
``` 
For more information, see http://docs.ceph.com/docs/master/rados/configuration/ceph-conf/

#### ceph.client.admin.keyring ####
```
[client.admin]
    key = AQARbphajODeCRBBPHpEZfDezGkP2r/BDzJPgg==
~                                                     
```
For more information, see http://docs.ceph.com/docs/master/rados/configuration/auth-config-ref/

### 
