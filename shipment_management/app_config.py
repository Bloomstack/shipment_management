
class SupportedProviderList(object):
    Undefined = "N/A"
    Fedex = 'FEDEX'


###################################
# Fedex:

# Used to switch from Fedex Test Server to Fedex Production Server
PRIMARY_FEDEX_DOC_NAME = "Fedex Test Server Config"


class FedexTestServerConfiguration(object):
    key = '0uSKxCgw6AZANfZ5'
    password = 'WFDeuKsHwGuplTgd7ESLK0FpB'
    account_number = '510087283'
    meter_number = '118747441'
    freight_account_number = '510087020'
    use_test_server = True

####################################


class SupportedDocTypes(object):
    ShipmentNote = 'DTI Shipment Note'
    ShipmentNoteItem = 'DTI Shipment Note Item'
    ShipmentPackage = 'DTI Shipment Package'
    FedexConfig = 'DTI Fedex Configuration'
    FedexShipment = 'DTI Fedex Shipment'
    FedexShipmentItem = 'DTI Fedex Shipment Item'
