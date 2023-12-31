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
        no_queries=10,
        query_min_size=200,
        query_max_size=1000,
        no_targets=800,
        target_min_size=10000,
        target_max_size=200000,
        query_name="datasets/query_sequences_8k.fasta",
        database_name="datasets/target_sequences_8k.fasta",
    )


# Run using `python3 ./utils/generate_synthetic_data.py`
if __name__ == "__main__":
    __main__()
