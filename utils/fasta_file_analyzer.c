// Warning: this is a work-in-progress tool, testing on the competition datasets has shown that the sequence length outputs are inaccurate.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char *argv[]) {
    if (argc != 2) {
        printf("Usage: %s <fasta_file>\n", argv[0]);
        return 1;
    }

    FILE *file = fopen(argv[1], "r");
    if (file == NULL) {
        perror("Error opening file");
        return 1;
    }

    char line[1024];
    int sequence_count = 0;
    int max_length = 0;
    int min_length = 0;
    int current_length = 0;
    char max_desc[1024] = ""; // Initialize to empty string
    char min_desc[1024] = ""; // Initialize to empty string
    int in_sequence = 0;

    char current_desc[1024]; // To store the current descriptor

    while (fgets(line, sizeof(line), file)) {
        if (line[0] == '>') {
            if (in_sequence) {
                if (current_length > max_length) {
                    max_length = current_length;
                    strcpy(max_desc, current_desc);
                }
                if ((current_length < min_length && current_length > 0) || min_length == 0) {
                    min_length = current_length;
                    strcpy(min_desc, current_desc);
                }
                current_length = 0;
            }
            sequence_count++;
            strcpy(current_desc, line); // Store the current descriptor
            in_sequence = 1;
        } else {
            current_length += strlen(line) - (line[strlen(line) - 1] == '\n' ? 1 : 0);
        }
    }

    // Check the last sequence in the file
    if (in_sequence) {
        if (current_length > max_length) {
            max_length = current_length;
            strcpy(max_desc, current_desc);
        }
        if ((current_length < min_length && current_length > 0) || min_length == 0) {
            min_length = current_length;
            strcpy(min_desc, current_desc);
        }
    }

    fclose(file);

    printf("Warning: this is a work-in-progress tool, testing on the competition datasets has shown that the sequence length outputs are inaccurate.\n");
    printf("Number of sequences: %d\n", sequence_count);
    printf("Maximum sequence length: %d\n", max_length);
    printf("Maximum sequence descriptor:\n%s", max_desc);
    printf("Minimum sequence length: %d\n", min_length);
    printf("Minimum sequence descriptor:\n%s", min_desc);

    return 0;
}
