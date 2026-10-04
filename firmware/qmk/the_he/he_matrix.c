// Analog matrix for THE: three 74HC4051 muxes, one per ADC pin, sharing three select lines.
// Row = mux (ADC pin), column = mux channel. he_map.h, generated from the routed boards, says which
// channels carry a sensor. Scan structure follows Boardloaf-HE (Cipulot / byungyoonc); the polarity-agnostic
// reading and per-key learned travel follow Hector.

#include "quantum.h"
#include "analog.h"
#include "print.h"

typedef struct {
    uint16_t rest;    // reading with the key up, measured at boot
    uint16_t travel;  // largest deflection seen so far
    uint16_t raw;
    bool     pressed;
} he_key_t;

static const pin_t   row_pins[MATRIX_ROWS / 2] = HE_ROW_PINS;
static const pin_t   sel_pins[3]               = HE_SEL_PINS;
static const uint8_t present_left[]            = HE_PRESENT_LEFT;
static const uint8_t present_right[]           = HE_PRESENT_RIGHT;
static const char   *names_left[MATRIX_ROWS / 2][MATRIX_COLS]  = HE_NAMES_LEFT;
static const char   *names_right[MATRIX_ROWS / 2][MATRIX_COLS] = HE_NAMES_RIGHT;

static adc_mux  adc_ch[MATRIX_ROWS / 2];
static he_key_t keys[MATRIX_ROWS / 2][MATRIX_COLS];
static const uint8_t *present;
static const char *(*names)[MATRIX_COLS];

static void select_channel(uint8_t ch) {
    for (uint8_t i = 0; i < 3; i++) {
        gpio_write_pin(sel_pins[i], (ch >> i) & 1);
    }
    wait_us(HE_SETTLE_US);
}

static uint16_t deflection(const he_key_t *k) {
    // the magnet may push the output either way, depending on how it sits in the switch
    return k->raw > k->rest ? k->raw - k->rest : k->rest - k->raw;
}

void matrix_init_custom(void) {
    bool left = is_keyboard_left();
    present   = left ? present_left : present_right;
    names     = left ? names_left : names_right;
    for (uint8_t i = 0; i < 3; i++) {
        gpio_set_pin_output(sel_pins[i]);
    }
    for (uint8_t r = 0; r < MATRIX_ROWS / 2; r++) {
        palSetLineMode(row_pins[r], PAL_MODE_INPUT_ANALOG);
        adc_ch[r] = pinToMux(row_pins[r]);
    }

    uint32_t sum[MATRIX_ROWS / 2][MATRIX_COLS] = {0};
    for (uint8_t n = 0; n < HE_CALIBRATION_SAMPLES; n++) {
        for (uint8_t c = 0; c < MATRIX_COLS; c++) {
            select_channel(c);
            for (uint8_t r = 0; r < MATRIX_ROWS / 2; r++) {
                sum[r][c] += adc_read(adc_ch[r]);
            }
        }
        wait_ms(1);
    }
    for (uint8_t r = 0; r < MATRIX_ROWS / 2; r++) {
        for (uint8_t c = 0; c < MATRIX_COLS; c++) {
            keys[r][c] = (he_key_t){.rest = sum[r][c] / HE_CALIBRATION_SAMPLES, .travel = HE_DEFAULT_TRAVEL};
            keys[r][c].raw = keys[r][c].rest;
        }
    }
}

bool matrix_scan_custom(matrix_row_t current_matrix[]) {
    bool changed = false;
    for (uint8_t c = 0; c < MATRIX_COLS; c++) {
        select_channel(c);
        for (uint8_t r = 0; r < MATRIX_ROWS / 2; r++) {
            if (!(present[r] & (1 << c))) {
                continue;
            }
            he_key_t *k = &keys[r][c];
            k->raw      = adc_read(adc_ch[r]);
            uint16_t d  = deflection(k);
            if (d > k->travel) {
                k->travel = d;
            }
            uint16_t act = MAX(k->travel * HE_ACTUATION_PCT / 100, HE_MIN_ACTUATION);
            uint16_t rel = k->travel * HE_RELEASE_PCT / 100;
            bool     now = k->pressed ? d > rel : d >= act;
            if (now != k->pressed) {
                k->pressed = now;
                changed    = true;
#ifdef HE_LOG_KEYS
                uprintf("%s %s  raw %u rest %u travel %u\n", names[r][c], now ? "down" : "up", k->raw, k->rest, k->travel);
#endif
            }
            if (now) {
                current_matrix[r] |= (matrix_row_t)1 << c;
            } else {
                current_matrix[r] &= ~((matrix_row_t)1 << c);
            }
        }
    }
    return changed;
}

// Prints every sensor's rest reading with a verdict. Run it with each half plugged in on its own: a wrong
// sensor pinout, a missing solder joint or a swapped part shows up as a reading stuck at a rail.
static void he_report(void) {
    uprintf("THE self test, %s half\n", is_keyboard_left() ? "left" : "right");
    uint8_t bad = 0;
    for (uint8_t r = 0; r < MATRIX_ROWS / 2; r++) {
        for (uint8_t c = 0; c < MATRIX_COLS; c++) {
            if (!(present[r] & (1 << c))) {
                continue;
            }
            const he_key_t *k = &keys[r][c];
            const char *verdict = k->rest < HE_REST_LOW    ? "LOW: output near GND (no supply, pinout, or short)"
                                  : k->rest > HE_REST_HIGH ? "HIGH: output near 3V3 (pinout, or open output)"
                                                           : "ok";
            bad += verdict[0] != 'o';
            uprintf("  mux %u ch %u  %-13s rest %4u  now %4u  travel %4u  %s\n", r, c, names[r][c], k->rest, k->raw, k->travel, verdict);
        }
    }
    uprintf("%u of 19 sensors look wrong\n", bad);
}

void housekeeping_task_kb(void) {
    static uint32_t next = HE_REPORT_DELAY_MS;
    if (next && timer_read32() >= next) {
        he_report();
#ifdef HE_REPORT_MS
        next += HE_REPORT_MS;
#else
        next = 0;
#endif
    }
    housekeeping_task_user();
}
