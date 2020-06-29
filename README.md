# sms-microapi
SMS microapi that connects with Twillo to allow users send sms.

This API requires python 3.++

### To Contribute:
* Create a personal fork of this repo
* Clone the fork to your PC using the command `git clone ~url to your fork~` 
* Change to the newly created directory on your PC
* Switch to develop branch using the command `git checkout develop`
* Create your virtual environment
* Install the RabbitMQ 
* Run the command `pip install -r requirements.txt`
* Make your changes
* Ensure you are working with an up to date version of the repo to avoid merge conflicts
* Before pushing, please pull the develop branch
* Run the command `pip freeze > requirements.txt` to update the requirements file with any dependency you used
* Push your changes to your fork `git push`
* Make a pull request to the Develop branch of the main repo


### When making a PR, please follow the guides below
* Please use the PR template when making an update
* Always comment your code for hard to understand feature
* APIs should carry annotation
* Your PR should contain descriptions so it's easier to read and merge 
* Test, Test and Test

### PACKAGES TO BE INSTALLED
* RABBITMQ DOWNLOAD -> https://www.rabbitmq.com/download.html
* To install infobip, run python -m pip install git+https://github.com/jonathan-golorry/infobip-api-python-client.git@python3