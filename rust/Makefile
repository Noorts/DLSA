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

# Uses cross on MacOS. See: https://github.com/cross-rs/cross.
.PHONY: build-linux-avx2
build-linux-avx2:
	@if [ $$(uname -s) = "Darwin" ]; then \
		RUSTFLAGS="-C target-feature=+avx2" cross build --release --target x86_64-unknown-linux-musl; \
	else \
		RUSTFLAGS="-C target-feature=+avx2" cargo build --release --target x86_64-unknown-linux-musl; \
	fi

.PHONY: build-darwin-avx2
build-macos-x86-avx2:
	RUSTFLAGS="-C target-feature=+avx2" cargo build --release --target x86_64-apple-darwin

.PHONY: build-native
build-native:
	RUSTFLAGS="-C target-cpu=native" cargo build --release
