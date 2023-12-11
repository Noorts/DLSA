.PHONY: bench
bench:
	sudo cset shield --cpu 1,2
	cset shield -e cargo bench
	sudo cset shield --reset
