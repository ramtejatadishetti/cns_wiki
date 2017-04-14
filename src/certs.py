from oscrypto import asymmetric
from certbuilder import CertificateBuilder, pem_armor_certificate


ROOT_CA_PRIVATE_KEY_PASSWORD = u'p'
ROOT_CA_PRIVATE_KEY_PATH = 'root_ca.key'
ROOT_CA_CERTIFICATE = 'root_ca.crt'
ROOT_CA_PUBLIC_KEY = 'root_ca_public.key'

CERTIFICATE_OUTPUT_DIRECTORY = "./certificates/"
CERTIFICATE_PREFIX = 'certificate_'
PUBLIC_KEY_STORE = "./public_keys/"


# Generate and save the key and certificate for the root CA
def create_certificate():
    root_ca_public_key, root_ca_private_key = asymmetric.generate_pair('rsa', bit_size=2048)

    with open('root_ca.key', 'wb') as f:
        f.write(asymmetric.dump_private_key(root_ca_private_key, u'p'))

    with open('root_ca_public.key', 'wb') as f:
        f.write(asymmetric.dump_public_key(root_ca_public_key, 'pem'))


    builder = CertificateBuilder(
        {
            u'country_name': u'US',
            u'state_or_province_name': u'Massachusetts',
            u'locality_name': u'Amherst',
            u'organization_name': u'Name Certifying service',
            u'common_name': u'NCS Root CA',
        },
        root_ca_public_key
    )
    builder.self_signed = True
    builder.ca = True
    root_ca_certificate = builder.build(root_ca_private_key)


    with open('root_ca.crt', 'wb') as f:
        f.write(pem_armor_certificate(root_ca_certificate))


    # Generate an end-entity key and certificate, signed by the root
    end_entity_public_key, end_entity_private_key = asymmetric.generate_pair('rsa', bit_size=2048)

    with open('ramteja_tadishetti_private.key', 'wb') as f:
        f.write(asymmetric.dump_private_key(end_entity_private_key,u'p'))

    with open('ramteja_tadishetti_public.key', 'wb') as f:
        f.write(asymmetric.dump_public_key(end_entity_public_key,'pem'))

    builder = CertificateBuilder(
        {
            u'country_name': u'US',
            u'state_or_province_name': u'Massachusetts',
            u'locality_name': u'Amherst',
            u'organization_name': u'Ramteja Tadishetti Corp',
            u'common_name': u'ramtejatadishetti',
        },
        end_entity_public_key
    )
    builder.issuer = root_ca_certificate
    #builder.set_extension( u'1.2.840.113549.1.1.1', 'ramteja', allow_deprecated=False)
    end_entity_certificate = builder.build(root_ca_private_key)

    with open('ramteja_tadishetti.crt', 'wb') as f:
        f.write(pem_armor_certificate(end_entity_certificate))

# return byte stream by freading from file 
def get_byte_stream_for_file(path_for_file):
    byteString = ""
    with open(path_for_file, 'r') as handle:
        byteString = handle.read()

    return byteString

    # create a client certificate given client_details 
def create_certificate_for_client(client_details):

    # load client public key
    path_for_client_public_key = PUBLIC_KEY_STORE + client_details['public_key']

    client_public_key = asymmetric.load_public_key\
                (get_byte_stream_for_file(path_for_client_public_key))

    root_ca_private_key = asymmetric.load_private_key\
                (get_byte_stream_for_file(ROOT_CA_PRIVATE_KEY_PATH), ROOT_CA_PRIVATE_KEY_PASSWORD)

    root_ca_public_key = asymmetric.load_public_key\
                (get_byte_stream_for_file(ROOT_CA_PUBLIC_KEY))

    root_ca_certificate = asymmetric.load_certificate\
                (get_byte_stream_for_file(ROOT_CA_CERTIFICATE))

    builder = CertificateBuilder(
        {
            u'country_name': client_details['country'].decode('utf-8'),
            u'state_or_province_name': client_details['state'].decode('utf-8'),
            u'locality_name': client_details['city'].decode('utf-8'),
            u'organization_name': client_details['name'].decode('utf-8'),
            u'common_name': client_details['domain_name'].decode('utf-8'),
        },
        client_public_key
    )

    dns_name = []
    dns_name.append(u'gns_provider')
    builder.issuer = root_ca_certificate
    
    builder.subject_alt_domains = dns_name
    #builder.set_extension(u'authority_information_access', u'1.3.6.1.5.5.7.1.1')

    client_certificate = builder.build(root_ca_private_key)
    client_certificate_name = CERTIFICATE_PREFIX + client_details['domain_name'].decode('utf-8') + ".crt"

    total_path = CERTIFICATE_OUTPUT_DIRECTORY + client_certificate_name

    with open(total_path, 'wb') as f:
        f.write(pem_armor_certificate(client_certificate))
    
    return client_certificate_name

if __name__ == '__main__':
    
    client_details = {}
    client_details['public_key'] = 'public_key.pem'
    client_details['country'] = 'India'
    client_details['state'] = 'Telangana'
    client_details['city'] = 'Hyderabad'
    client_details['name'] = 'Ramteja Tadishetti Corp'
    client_details['domain_name'] = 'rtadishetti'

    #create_certificate()
    create_certificate_for_client(client_details)
    
    
