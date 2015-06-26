#!/bin/bash
cd /usr/share/easy-rsa/

source vars
./clean-all 
./build-ca --batch androlyze_ca
./build-dh
./build-key-server --batch androlyze_server
./build-key --batch androlyze_client


mv keys/ca.crt keys/androlyze_ca.pem
mv keys/ca.key keys/androlyze_ca.key
cp keys/* keys_androlyze/