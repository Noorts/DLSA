#include <stdint.h>
#include <stddef.h>

struct Result
{
  char *query_ptr;
  char *target_ptr;
};

void test_binding();
struct Result test_write(char *buf, size_t size);
struct Result find_alignment_parallel(char *query, char *target, size_t threads);
struct Result find_alignment_sequential(char *query, char *target);
struct Result find_alignment_sequential_straight(char *query, char *target);
struct Result find_alignment_simd(char *query, char *target);
void free_alignment_result(char *query, char *target);
void free_c_string(char *str);