/* Standalone read-only RP2040 SPI NOR diagnostics; not Pico Fusion proprietary firmware. */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include "pico/stdlib.h"
#include "hardware/spi.h"
#define SPI_PORT spi0
#define PIN_MISO 16
#define PIN_CS 17
#define PIN_SCK 18
#define PIN_MOSI 19
#define CHUNK 128
#define MAX_ADDR 0xFFFFFFu
static inline void cs(bool active) { gpio_put(PIN_CS, !active); }
static void init_spi(void) {
    spi_init(SPI_PORT, 1000 * 1000);
    spi_set_format(SPI_PORT, 8, SPI_CPOL_0, SPI_CPHA_0, SPI_MSB_FIRST);
    gpio_set_function(PIN_MISO, GPIO_FUNC_SPI);
    gpio_set_function(PIN_SCK, GPIO_FUNC_SPI);
    gpio_set_function(PIN_MOSI, GPIO_FUNC_SPI);
    gpio_init(PIN_CS);
    gpio_set_dir(PIN_CS, GPIO_OUT);
    cs(false);
}
static void read_id(uint8_t out[3]) {
    uint8_t command = 0x9F;
    cs(true);
    spi_write_blocking(SPI_PORT, &command, 1);
    spi_read_blocking(SPI_PORT, 0xFF, out, 3);
    cs(false);
}
static void read_chunk(uint32_t addr, uint8_t *dst, size_t count) {
    uint8_t command[4] = {0x03, addr >> 16, addr >> 8, addr};
    cs(true);
    spi_write_blocking(SPI_PORT, command, 4);
    spi_read_blocking(SPI_PORT, 0xFF, dst, count);
    cs(false);
}
static uint32_t crc_next(uint32_t crc, uint8_t value) {
    crc ^= value;
    for (int i = 0; i < 8; i++)
        crc = (crc >> 1) ^ ((crc & 1) ? 0xEDB88320u : 0);
    return crc;
}
static void process(char *line) {
    if (!strcmp(line, "ID")) {
        uint8_t id[3]; read_id(id);
        printf("ID %02X%02X%02X\n", id[0], id[1], id[2]);
        return;
    }
    if (!strcmp(line, "HELP")) {
        puts("COMMANDS ID | READ <offset_decimal> <length_decimal> | HELP");
        return;
    }
    if (strncmp(line, "READ ", 5)) { puts("ERR unknown_command"); return; }
    char *p = line + 5, *end;
    unsigned long addr = strtoul(p, &end, 10);
    if (p == end || *end != ' ') { puts("ERR syntax"); return; }
    p = end + 1;
    unsigned long length = strtoul(p, &end, 10);
    if (p == end || *end || !length || addr > MAX_ADDR ||
        length > (unsigned long)(MAX_ADDR + 1u - addr)) {
        puts("ERR range_or_syntax"); return;
    }
    uint8_t buf[CHUNK];
    uint32_t crc = 0xFFFFFFFFu;
    uint32_t pos = (uint32_t)addr, remaining = (uint32_t)length;
    while (remaining) {
        uint32_t n = remaining > CHUNK ? CHUNK : remaining;
        read_chunk(pos, buf, n);
        printf("DATA %lu ", (unsigned long)pos);
        for (uint32_t i = 0; i < n; i++) {
            printf("%02X", buf[i]);
            crc = crc_next(crc, buf[i]);
        }
        putchar('\n');
        pos += n;
        remaining -= n;
    }
    printf("DONE %08lX %lu\n", (unsigned long)(crc ^ 0xFFFFFFFFu), length);
}
int main(void) {
    stdio_init_all();
    init_spi();
    char line[96]; size_t used = 0;
    while (true) {
        int ch = getchar_timeout_us(0);
        if (ch == PICO_ERROR_TIMEOUT) { sleep_ms(1); continue; }
        if (ch == '\r' || ch == '\n') {
            if (used) { line[used] = '\0'; process(line); used = 0; }
        } else if (ch >= 32 && ch <= 126) {
            if (used < sizeof(line) - 1) line[used++] = (char)ch;
            else { used = 0; puts("ERR line_too_long"); }
        }
    }
}
