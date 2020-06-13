test:
	safety check -r requirements.txt
	bandit plugin.py

lint:
	pylint twilio_plugin

format:
	black --line-length 120 twilio_plugin

build:
	mbc build
