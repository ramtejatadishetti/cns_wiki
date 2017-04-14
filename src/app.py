from flask import Flask, flash, render_template, send_from_directory, request
from werkzeug.utils import secure_filename
from flask.ext.mysql import MySQL
import os

import threading
import time
from certs import create_certificate_for_client
from send_mail import send_mail_from_admin
import uuid

ACCESS_DENIED = "Access denied"
INDEX_FILE = "index.html"
VALIDATION_FAILURE = "Validation failed please retry again"
MYSQL_DATABASE_USER = 'root'
MYSQL_DATABASE_PASSWORD = 'cns'
MYSQL_DATABASE_DB = 'ncs'
MYSQL_DATABASE_HOST = 'localhost'
TABLE_NAME = 'ncs.user_data'
MYSQL_DATABASE_PORT = 3306
USER_ID_FIELD_NAME = 'user_id'
IDENTIFIER_FIELD_NAME = 'identifier'
NAME_CONFLICT_ERROR= 'Name Conflict, please try with another name'
KEY_PREFIX = 'cert_'
KEY_SUFFIX = '.crt'
PROOF_PREFIX = 'proof_'
PROOF_SUFFIX = '.proof'




# TODO find out when to intialize these stuff
app = Flask(__name__, template_folder='template')
mysql =  MySQL()
cursor = ""


# placeholder function to do server side validation
# returns 1 on success
def validate_fields(data_request):
    return 1


# helper function to check if any entry exists with same name
def check_name_conflict(domain_name):
    query_statement = "SELECT " + USER_ID_FIELD_NAME + " FROM " + TABLE_NAME + " WHERE " +  IDENTIFIER_FIELD_NAME + "='%s'" % (domain_name)

    conn = mysql.connect()
    cursor = conn.cursor()

    result = cursor.execute(query_statement)
    data = cursor.fetchone()
    if data == None:
        return False

    else:
        return True

# Insert fields into database
# returns 1 on success
def insert_fields_into_database(data_request):
    # read all variables into local

    first_name = data_request.form['first_name']
    last_name = data_request.form['last_name']

    email = data_request.form['email']
    phone = data_request.form['phone']

    address = data_request.form['address'] + " "
    address += data_request.form['city'] + " "
    address += data_request.form['state'] + " "
    address += str(data_request.form['zip'])

    identifier = data_request.form['website']
    gns_provider = data_request.form['gns_provider']
    description = data_request.form['comment']

    file1 = data_request.files['keyInput']
    file2 = data_request.files['proofInput']

    filename1 = ""
    filename2 = ""

    # TODO change this code to get a valid file name
    if file1:
        filename1 = KEY_PREFIX + identifier + KEY_SUFFIX
        file1.save(os.path.join(app.config['UPLOAD_KEY'], filename1))
    if file2:
        filename2 = PROOF_PREFIX + identifier + PROOF_SUFFIX
        file2.save(os.path.join(app.config['UPLOAD_PROOF'], filename2))
    
    query_statement = " INSERT into " + TABLE_NAME + " " + \
                        " (first_name,last_name, email, mobile, address, public_key, proof, identifier, gns_provider, description, verified) " + \
                        " VALUES ('" + first_name + "' , '"+ last_name +"', '"+ email + "', '" + phone + "', '" + address +"' , '" + filename1 +"','" \
			+ filename2 + "', '"+ identifier + "', '"+ gns_provider +"', '"+ description +"',0)"   

    conn = mysql.connect()
    cursor = conn.cursor()
    result = cursor.execute(query_statement)
    conn.commit()

    return 1,filename1

#validate path obtained while serving static pages 
def validate_uri(path):
    return 1

# send static javascript files  
@app.route('/js/<path:path>')
def send_js(path):
    if (validate_uri(path)  == 1 ) :
        return send_from_directory('js', path)
    else :
        return ACCESS_DENIED

# send static css files 
@app.route('/css/<path:path>')
def send_css(path):
    if (validate_uri(path)  == 1 ) :
        return send_from_directory('css', path)
    else :
        return ACCESS_DENIED

# send index file on request 
@app.route('/')
def hello():
    return render_template(INDEX_FILE)


# utility function read values from request
def get_details_from_request(data_request, file_name):

    client_details= {}
    client_details['name'] = data_request.form['first_name'] + data_request.form['last_name']
    client_details['state'] = data_request.form['state']
    client_details['mail'] = data_request.form['email']
    client_details['city'] = data_request.form['city']
    client_details['domain_name'] = data_request.form['website']
    client_details['public_key'] = file_name

    
    #TODO remove hard_coding of country
    client_details['country'] = "US"

    return client_details


# create certificate and mail to the client
def send_certificate_to_client(client_details):
    time.sleep(5)
    certificate_file = create_certificate_for_client(client_details)
    send_mail_from_admin(certificate_file, client_details['mail'])

# helper function to resolve error_codes to names
def get_reason_for_error_code(error_code):
    if error_code == 2:
        return "Name Conflict, please try with another name"
    else:
        return "Unknown error has occured please try again later"



# handle client request
def handle_client_request(request):
    # insert data into database
    insert_result = insert_fields_into_database(request)

    if (insert_result == 1):
        # get client details in required_format
        client_details = get_details_from_request(request)
        t = threading.Thread(target=send_certificate_to_client, args=(client_details,))
        t.start()

    else:
        print "Unknown error has occured while insertinginto database \n"


# receive and process the data 
@app.route('/submitdata',  methods=['POST'])
def process_request():

    if request.method == 'POST':
        # do server validation of fields 
        if ( validate_fields(request) == 1) :

            #check for name conflict
            if check_name_conflict(request.form['website']) == True:
                 return NAME_CONFLICT_ERROR

            insert_result = insert_fields_into_database(request)

            if (insert_result[0] == 1):

                # get client details in required_format
                client_details = get_details_from_request(request, insert_result[1])
                t = threading.Thread(target=send_certificate_to_client, args=(client_details,))
                t.start()

                return "Success"

            else:
                return "Unknown error has occured while inserting into database \n"

        else :
            return VALIDATION_FAILURE


# init mysql config
def init_mysql_config():
    app.config['MYSQL_DATABASE_USER'] = MYSQL_DATABASE_USER
    app.config['MYSQL_DATABASE_PASSWORD'] = MYSQL_DATABASE_PASSWORD
    app.config['MYSQL_DATABASE_DB'] = MYSQL_DATABASE_DB
    app.config['MYSQL_DATABASE_HOST'] = MYSQL_DATABASE_HOST
    app.config['MYSQL_DATABASE_PORT'] = MYSQL_DATABASE_PORT
    mysql.init_app(app)
    

# main method 
if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['UPLOAD_FOLDER'] = "./"
    app.config['UPLOAD_PROOF'] = "./proof/"
    app.config['UPLOAD_KEY'] = "./public_keys/"
    init_mysql_config()
    app.run(host='0.0.0.0', port=80)

