import random


def generate_synthetic_data(
    no_queries, query_max_size, query_min_size, no_targets, target_min_size, target_max_size, query_name, database_name
):
    def generate_sequences(no_sequences, min_size, max_size, filename):
        with open(filename, "w") as file:
            for i in range(1, no_sequences + 1):
                seq_length = random.randint(min_size, max_size)
                sequence = "".join(random.choices(["A", "T", "C", "G"], k=seq_length))
                file.write(f">seq{i}\n{sequence}\n")

    # Generate query sequences
    generate_sequences(no_queries, query_min_size, query_max_size, query_name)

    # Generate target sequences
    generate_sequences(no_targets, target_min_size, target_max_size, database_name)


def __main__():
    generate_synthetic_data(
        no_queries=100,
        query_max_size=1000,
        query_min_size=200,
        no_targets=100,
        target_min_size=1000,
        target_max_size=5000,
        query_name="query_sequences.fasta",
        database_name="target_sequences.fasta",
    )


# Run using `python3 ./utils/generate_synthetic_data.py`
if __name__ == "__main__":
    __main__()
