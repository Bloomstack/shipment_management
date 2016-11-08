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

# 3. Installation

## 3.1. Clone app from git

Go to folder:
```
cd frappe-bench
```

Execute command:
```
bench get-app shipment_management https://github.com/safo-bora/shipment_management.git

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

# 4.Deployment:
Fedex Config should be created

in progress

# 5. Shipment providers

## 5.1 FedEx

### Overview
FedEx Corporation is a US multinational courier delivery services company.
The company is known for its overnight shipping service, but also for pioneering a system 
that could track packages and provide real-time updates on package location.


### Status Check Web Page
Added web page for customer to provide possibility to check status by tracking number

{site_path}\fedex.html

# 6. Automation Testing
Module was covered with functional testing. 

For run tests you should execute command:

```
bench run-tests --app shipment_management
```

# 7. Permissions
in progress



