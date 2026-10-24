// Analog matrix for Tot-HE-m: three 74HC4051 muxes, one per ADC pin, sharing three select lines.
// Row = mux (ADC pin), column = mux channel. he_map.h, generated from the routed boards, says which
// channels carry a sensor. Scan structure follows Boardloaf-HE (Cipulot / byungyoonc); the polarity-agnostic
// reading and per-key learned travel follow Hector.

#include "quantum.h"
#include "analog.h"
#include "print.h"
#include "send_string.h"

typedef struct {
    uint16_t rest;    // reading with the key up, measured at boot
    uint16_t travel;  // largest deflection seen so far
    uint16_t raw;
    uint16_t lo, hi;  // lowest and highest reading since the last report, for the typed self test
    uint8_t  pending; // scans in a row that disagree with the current state
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
#ifdef HE_TYPE_REPORT
#    ifndef HE_PRESS_WINDOW_MS
#        define HE_PRESS_WINDOW_MS 45000
#    endif
static uint16_t presses[MATRIX_ROWS / 2][MATRIX_COLS];
static uint8_t  order[64][2];   // row and column of each press, in the order they happened
static uint8_t  order_n;
#endif
static const char *(*names)[MATRIX_COLS];

static void select_channel(uint8_t ch) {
    for (uint8_t i = 0; i < 3; i++) {
        gpio_write_pin(sel_pins[i], (ch >> i) & 1);
    }
    wait_us(HE_SETTLE_US);
}

// several conversions per channel, averaged, to keep ADC noise below the actuation points
static uint16_t he_read(adc_mux ch) {
    uint32_t sum = 0;
    for (uint8_t i = 0; i < HE_OVERSAMPLE; i++) {
        sum += adc_read(ch);
    }
    return sum / HE_OVERSAMPLE;
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
                sum[r][c] += he_read(adc_ch[r]);
            }
        }
        wait_ms(1);
    }
    for (uint8_t r = 0; r < MATRIX_ROWS / 2; r++) {
        for (uint8_t c = 0; c < MATRIX_COLS; c++) {
            // no assumed travel: a key fires at HE_MIN_ACTUATION until it has been pressed and learns its own
            keys[r][c] = (he_key_t){.rest = sum[r][c] / HE_CALIBRATION_SAMPLES, .lo = 0xFFFF};
            keys[r][c].raw = keys[r][c].rest;
        }
    }
}

bool matrix_scan_custom(matrix_row_t current_matrix[]) {
    static uint8_t scans;
    uint8_t        n = 0, jumped = 0;
    for (uint8_t c = 0; c < MATRIX_COLS; c++) {
        select_channel(c);
        for (uint8_t r = 0; r < MATRIX_ROWS / 2; r++) {
            if (!(present[r] & (1 << c))) {
                continue;
            }
            he_key_t *k = &keys[r][c];
            k->raw      = he_read(adc_ch[r]);
            k->lo       = MIN(k->lo, k->raw);
            k->hi       = MAX(k->hi, k->raw);
            n++;
            jumped += deflection(k) >= HE_MIN_ACTUATION;
        }
    }
    // every channel dips at once now and then; a real chord moves a few keys, so a scan where most moved is dropped
    if (jumped * 2 > n) {
        return false;
    }
    bool changed = false;
    scans++;
    for (uint8_t r = 0; r < MATRIX_ROWS / 2; r++) {
        for (uint8_t c = 0; c < MATRIX_COLS; c++) {
            if (!(present[r] & (1 << c))) {
                continue;
            }
            he_key_t *k   = &keys[r][c];
            uint16_t  d   = deflection(k);
            uint16_t  act = MAX(k->travel * HE_ACTUATION_PCT / 100, HE_MIN_ACTUATION);
            uint16_t  rel = MAX(k->travel * HE_RELEASE_PCT / 100, HE_MIN_RELEASE);
            bool      now = k->pressed ? d > rel : d >= act;
            k->pending    = now != k->pressed ? k->pending + 1 : 0;
            if (k->pending >= HE_DEBOUNCE_SCANS) {
                k->pressed = now;
                k->pending = 0;
                changed    = true;
#ifdef HE_TYPE_REPORT
                if (now) {
                    presses[r][c]++;
                    if (order_n < 64) {
                        order[order_n][0] = r;
                        order[order_n++][1] = c;
                    }
                }
#endif
#ifdef HE_LOG_KEYS
                uprintf("%s %s  raw %u rest %u travel %u\n", names[r][c], now ? "down" : "up", k->raw, k->rest, k->travel);
#endif
            }
            if (k->pressed && d > k->travel) {
                k->travel = d;   // learnt only from confirmed presses, so a glitch cannot raise it
            }
            if (!k->pressed && d < HE_MIN_RELEASE && scans % 64 == 0) {
                k->rest += k->raw > k->rest ? 1 : k->raw < k->rest ? -1 : 0;   // follows slow drift at rest
            }
            if (k->pressed) {
                current_matrix[r] |= (matrix_row_t)1 << c;
            } else {
                current_matrix[r] &= ~((matrix_row_t)1 << c);
            }
        }
    }
    return changed;
}

#ifdef HE_TYPE_REPORT
// The same report typed into whatever has focus, for a computer without the QMK console. The first one gives the
// rest readings; the second, HE_PRESS_WINDOW_MS later, the largest deflection and press count per sensor and the
// order in which presses were detected, so a swapped or doubled key shows as an unexpected name in the list.
static void he_type_report(bool presses_done) {
    send_string(presses_done ? "\nTot-HE-m press test, " : "\nTot-HE-m rest test, ");
    send_string(is_keyboard_left() ? "left half\n" : "right half\n");
    for (uint8_t r = 0; r < MATRIX_ROWS / 2; r++) {
        for (uint8_t c = 0; c < MATRIX_COLS; c++) {
            if (!(present[r] & (1 << c))) {
                continue;
            }
            const he_key_t *k = &keys[r][c];
            send_string(names[r][c]);
            send_string("  mux");
            send_string(get_u16_str(r, ' '));
            send_string(" ch");
            send_string(get_u16_str(c, ' '));
            send_string("  rest");
            send_string(get_u16_str(k->rest, ' '));
            if (presses_done) {
                send_string("  low");
                send_string(get_u16_str(k->lo, ' '));
                send_string("  high");
                send_string(get_u16_str(k->hi, ' '));
                send_string("  max");
                send_string(get_u16_str(k->travel, ' '));
                send_string("  presses");
                send_string(get_u16_str(presses[r][c], ' '));
            } else {
                send_string("  noise");
                send_string(get_u16_str(k->hi - k->lo, ' '));
                send_string(k->rest < HE_REST_LOW ? "  LOW" : k->rest > HE_REST_HIGH ? "  HIGH" : "  ok");
            }
            send_string("\n");
        }
    }
    if (presses_done) {
        send_string("order:");
        for (uint8_t i = 0; i < order_n; i++) {
            send_string(" ");
            send_string(names[order[i][0]][order[i][1]]);
        }
        send_string("\n");
    } else {
        send_string("press every key once now, in order; the result follows in a while\n");
    }
}

void housekeeping_task_kb(void) {
    static uint8_t step;
    if (step < 2 && timer_read32() >= HE_REPORT_DELAY_MS + step * HE_PRESS_WINDOW_MS) {
        he_type_report(step++);
        for (uint8_t r = 0; r < MATRIX_ROWS / 2; r++) {
            for (uint8_t c = 0; c < MATRIX_COLS; c++) {
                keys[r][c].lo = 0xFFFF;
                keys[r][c].hi = 0;
            }
        }
    }
    housekeeping_task_user();
}
#else
// Prints every sensor's rest reading with a verdict. Run it with each half plugged in on its own: a wrong
// sensor pinout, a missing solder joint or a swapped part shows up as a reading stuck at a rail.
static void he_report(void) {
    uprintf("Tot-HE-m self test, %s half\n", is_keyboard_left() ? "left" : "right");
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
#endif
