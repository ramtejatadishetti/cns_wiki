#/bin/bash

#Generate private key 
openssl genrsa -out pre_key.pem 2048


#Get public key
openssl rsa -in pre_key.pem -pubout > public_key.pem

#change the private key to pkcs8 specification
openssl pkcs8 -topk8 -inform PEM -outform PEM -in pre_key.pem -out private_key.pem -nocrypt

#delete pre_key
rm pre_key.pem
