CONTAINER = terminal_system
PUSH_TAG = latest

build:
	echo Building $(CONTAINER):$(PUSH_TAG)
	docker build --rm -t $(CONTAINER):$(PUSH_TAG) .
run:
	echo Run bash $(CONTAINER):$(PUSH_TAG)
	docker run --rm -ti -v ${PWD}:/task $(CONTAINER):$(PUSH_TAG)