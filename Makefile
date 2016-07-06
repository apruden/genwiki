GAE_HOME=/home/alex/google_appengine

deps:
	mkdir lib || pip install -t lib -r requirements.txt

run:
	python $(GAE_HOME)/dev_appserver.py .

deploy:
	cd .. && python $(GAE_HOME)/appcfg.py update genwiki
