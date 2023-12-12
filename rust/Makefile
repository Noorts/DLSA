.PHONY: bench
bench:
	sudo cset shield --cpu 1,2
	cset shield -e cargo bench
	sudo cset shield --reset

.PHONY: run
run:
	sudo cset shield --cpu 1,2
	cset shield -e -- env RUSTFLAGS="-C target-cpu=native" cargo run --release
	sudo cset shield --reset
