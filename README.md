# 1. Shipment Management Overview

Shipment Management Process

# 2. License

The MIT License

Copyright (c) 2016 DigiThinkIt Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy of 
this software and associated documentation files (the "Software"), to deal in the 
Software without restriction, including without limitation the rights to use, copy, 
modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to 
permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH 
THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# 3. Installation/ Uninstall

## 3.1. Clone app from git

Go to folder:
```
cd frappe-bench
```

Execute command:
```
bench get-app shipment_management https://github.com/DigiThinkIT/shipment_management.git

```

## 3.2. Install app for your site
```
bench --site {site_name} install-app shipment_management
```

_Note: All sites are located in frappe-bench/sites folder_

##  3.3. Restart bench
```
bench restart
```

## 3.4. Check that everything has been installed successful

New application is present in application list

```
bench list-apps
```

## 3.5. Uninstall
```
bench uninstall-app shipment_management
```

# 4.Config:
File _app-config_ is used for general fedex configuration. 

PRIMARY_FEDEX_DOC_NAME - Used to switch from Fedex Test Server to Fedex Production Server

# 5.DocTypes:

- DTI Shipment Note (Primary Doc Type)
- DTI Shipment Note Item (Items from Delivery Note, Table can be customised)
- DTI Shipment Package (Physical shipment box)
- DTI Fedex Shipment Configuration (Configuration DocType for Fedex Connection)
- DTI Fedex Shipment (Shipment information, with tracking number, labels and etc.)
- DTI Fedex Shipment Item (Items from Shipment Note, Table Read-Only)

# 6. Supported Shipment providers

## 6.1 FedEx

### Overview
FedEx Corporation is a US multinational courier delivery services company.
The company is known for its overnight shipping service, but also for pioneering a system 
that could track packages and provide real-time updates on package location.


### Status Check Web Page
Added web page for customer to provide possibility to check status by tracking number

{site_path}\shipment_tracking.html

# 7. Automation Testing
Module was covered with functional testing. 

For run tests you should execute command:

```
bench run-tests --app shipment_management
```
or
```
bench run-tests --module "shipment_management.shipment_management.test_shipment_management"
```

# 8. Permissions
- Shipment Manager
- Shipment User

# 9. Debug/testing:
Debug command for set fedex status.

Example statuses:

AA - At Airport
PL - Plane Landed
AD - At Delivery
PM - In Progress
AF - At FedEx Facility
PU - Picked Up
AP - At Pickup
PX - Picked up 
AR - Arrived at
RR - CDO Requested
AX - At USPS facility
RM - CDO Modified
CA - Shipment Canceled
RC - CDO Cancelled
CH - Location Changed
RS - Return to Shipper
DD - Delivery Delay
DE - Delivery Exception
DL - Delivered
DP - Departed FedEx Location
SE - Shipment Exception
DS - Vehicle dispatched
SF - At Sort Facility
DY - Delay
SP - Split status - multiple statuses
EA - Enroute to Airport delay
TR - Transfer
