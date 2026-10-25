// Analog matrix for Tot-HE-m: three 74HC4051 muxes, one per ADC pin, sharing three select lines.
// Row = mux (ADC pin), column = mux channel. he_map.h, generated from the routed boards, says which
// channels carry a sensor. Scan structure follows Boardloaf-HE (Cipulot / byungyoonc); the polarity-agnostic
// reading and per-key learned travel follow Hector.

#include <math.h>
#include "quantum.h"
#include "analog.h"
#include "print.h"
#include "send_string.h"
#include "he_config.h"

typedef struct {
    uint16_t rest;    // reading with the key up, measured at boot
    uint16_t travel;  // full swing in counts, learnt from bottom-outs while typing (learn_travel), 0 until then
    uint16_t peak;    // deepest deflection of the press under way, from first actuation until the key is back up
    uint16_t low_min, low_max; // shallowest and deepest of the short presses in a row counted by low_streak
    uint16_t raw;
    uint16_t stick;   // controller layer: depth in 0.01 mm counted from the edge of the resting noise (he_stick_depth)
    uint8_t  noise;   // spread of the readings at rest, measured at boot; movement starts beyond it
    uint16_t lo, hi;  // lowest and highest reading since the last report, for the typed self test
    uint16_t extreme; // rapid trigger: deepest depth while pressed, shallowest since the last release, 0.01 mm
    uint8_t  pending; // scans in a row that disagree with the current state
    bool     pressed;
    bool     rt_zone; // rapid trigger: actuated since the key last came back above the release point
    bool     cycle;   // a press is under way: actuated, not yet back above the release point
    uint8_t  low_streak; // presses in a row that stopped short of the learnt bottom
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

// Key depth from the reading. The field at the sensor goes with the inverse cube of the magnet's distance, so the
// share of a key's full swing grows slowly at the top of the press and fast at the bottom. depth_lut maps that
// share, in 64ths, to depth in 0.01 mm, from the travel and bottom-out gap in config.h; filled once at boot.
static uint16_t depth_lut[65];

static void depth_lut_init(void) {
    const float top = (HE_GAP_DMM + HE_TRAVEL_DMM) / 10.0f, bottom = HE_GAP_DMM / 10.0f;
    const float b_top = 1 / (top * top * top), b_bottom = 1 / (bottom * bottom * bottom);
    for (uint8_t i = 0; i <= 64; i++) {
        float b      = b_top + (b_bottom - b_top) * i / 64;
        depth_lut[i] = (uint16_t)((top - cbrtf(1 / b)) * 100 + 0.5f);
    }
}

// Bottom-out learning, run when a press ends (the key is back above the release point). A press whose deepest point
// comes within HE_BOTTOM_PCT of the learnt travel is a bottom-out, and the travel moves 1/HE_TRAVEL_SMOOTHING of the
// way to it, so it settles on where the key regularly bottoms and one odd press barely moves it. Shorter presses are
// ignored, unless HE_LOW_STREAK of them come in a row that all stop within HE_LOW_SPREAD_PCT of each other (a weaker
// magnet, a swapped switch, which bottom out shallower but always at the same spot): then the deepest of them becomes
// the travel. Partial presses on purpose, typing lightly or steering with the controller layer, vary too much to
// count. Learnt travel is saved to EEPROM by he_travel_task and loaded at boot by he_travel_load.
static bool travel_dirty;

static void learn_travel(he_key_t *k) {
    if (k->peak < HE_MIN_TRAVEL) {
        return;   // a tap too light to say anything about the bottom
    }
    if (!k->travel || k->peak * 100 >= k->travel * HE_BOTTOM_PCT) {
        k->travel     = k->travel ? k->travel + ((int)k->peak - (int)k->travel) / HE_TRAVEL_SMOOTHING : k->peak;
        k->low_streak = 0;
    } else {
        if (!k->low_streak) {
            k->low_min = k->low_max = k->peak;
        }
        k->low_min = MIN(k->low_min, k->peak);
        k->low_max = MAX(k->low_max, k->peak);
        if ((k->low_max - k->low_min) * 100 > k->low_max * HE_LOW_SPREAD_PCT) {
            k->low_streak = 1;   // too spread to be one bottom: start a new streak from this press
            k->low_min = k->low_max = k->peak;
            return;
        }
        if (++k->low_streak < HE_LOW_STREAK) {
            return;
        }
        k->travel     = k->low_max;
        k->low_streak = 0;
    }
    travel_dirty = true;
}

// depth in 0.01 mm of a key deflected by d counts out of a full swing of `travel` counts
static uint16_t depth(uint16_t d, uint16_t travel) {
    uint32_t s = MIN((uint32_t)d * 4096 / travel, 4096);
    uint16_t i = s >> 6, f = s & 63;
    return i == 64 ? depth_lut[64] : depth_lut[i] + (uint32_t)(depth_lut[i + 1] - depth_lut[i]) * f / 64;
}

void matrix_init_custom(void) {
    bool left = is_keyboard_left();
    present   = left ? present_left : present_right;
    depth_lut_init();
    names     = left ? names_left : names_right;
    for (uint8_t i = 0; i < 3; i++) {
        gpio_set_pin_output(sel_pins[i]);
    }
    for (uint8_t r = 0; r < MATRIX_ROWS / 2; r++) {
        palSetLineMode(row_pins[r], PAL_MODE_INPUT_ANALOG);
        adc_ch[r] = pinToMux(row_pins[r]);
    }

    uint32_t sum[MATRIX_ROWS / 2][MATRIX_COLS] = {0};
    uint16_t lo[MATRIX_ROWS / 2][MATRIX_COLS], hi[MATRIX_ROWS / 2][MATRIX_COLS] = {{0}};
    memset(lo, 0xFF, sizeof(lo));
    for (uint8_t n = 0; n < HE_CALIBRATION_SAMPLES; n++) {
        for (uint8_t c = 0; c < MATRIX_COLS; c++) {
            select_channel(c);
            for (uint8_t r = 0; r < MATRIX_ROWS / 2; r++) {
                uint16_t v = he_read(adc_ch[r]);
                sum[r][c] += v;
                lo[r][c] = MIN(lo[r][c], v);
                hi[r][c] = MAX(hi[r][c], v);
            }
        }
        wait_ms(1);
    }
    for (uint8_t r = 0; r < MATRIX_ROWS / 2; r++) {
        for (uint8_t c = 0; c < MATRIX_COLS; c++) {
            // travel 0: HE_ASSUMED_TRAVEL stands in until he_travel_load or a bottom-out sets it
            keys[r][c] = (he_key_t){.rest = sum[r][c] / HE_CALIBRATION_SAMPLES, .lo = 0xFFFF};
            keys[r][c].raw   = keys[r][c].rest;
            keys[r][c].noise = MIN(MAX(hi[r][c] - lo[r][c], HE_STICK_NOISE_MIN) + 1, HE_STICK_NOISE_MAX);
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
            jumped += deflection(k) >= HE_GLITCH_COUNTS;
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
            uint16_t  pos = depth(d, MAX(k->travel ? k->travel : HE_ASSUMED_TRAVEL, d));
            // the stick's depth is zeroed where the reading leaves the resting noise, so it rises from 0 at the first
            // movement the sensor can tell apart, and still reaches the bottom at the full swing
            uint16_t  full = MAX(k->travel ? k->travel : HE_ASSUMED_TRAVEL, d);
            k->stick       = d > k->noise ? depth(d - k->noise, full - k->noise) : 0;
            bool      up  = pos <= he_config.release_dmm * 10 || d <= HE_MIN_RELEASE;   // back above the release point
            bool      now;
            if (!he_config.rapid_trigger) {
                now = k->pressed ? !up : pos >= he_config.actuation_dmm * 10 && d >= HE_MIN_ACTUATION;
            } else {
                // the first press needs the actuation point; after that the key lets go as soon as it rises by the
                // release sensitivity from its deepest point, and fires again as soon as it sinks by the press
                // sensitivity from its shallowest point, until it comes back above the release point
                if (up) {
                    k->rt_zone = false;
                }
                if (k->pressed) {
                    k->extreme = MAX(k->extreme, pos);
                    now        = !up && k->extreme - pos < he_config.rt_release_dmm * 10;
                } else {
                    k->extreme = MIN(k->extreme, pos);
                    now        = k->rt_zone ? pos >= k->extreme + he_config.rt_press_dmm * 10
                                            : pos >= he_config.actuation_dmm * 10 && d >= HE_MIN_ACTUATION;
                }
            }
            k->pending = now != k->pressed ? k->pending + 1 : 0;
            if (k->pending >= HE_DEBOUNCE_SCANS) {
                k->pressed = now;
                k->pending = 0;
                k->extreme = pos;   // rapid trigger measures the next move from here
                k->rt_zone |= now;
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
                uprintf("%s %s  raw %u rest %u travel %u depth %u.%02u mm\n", names[r][c], now ? "down" : "up", k->raw, k->rest, k->travel, pos / 100, pos % 100);
#endif
            }
            k->cycle |= k->pressed;
            if (k->cycle) {
                k->peak = MAX(k->peak, d);
                if (up && !k->pressed) {
                    learn_travel(k);
                    k->cycle = false;
                    k->peak  = 0;
                }
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

// the controller layer's depth in 0.01 mm for the key at matrix position (row, col), counted from the edge of its
// resting noise; 0 for an empty channel or a key on the other half
uint16_t he_stick_depth(uint8_t row, uint8_t col) {
    uint8_t first = is_keyboard_left() ? 0 : MATRIX_ROWS / 2;
    if (row < first || row >= first + MATRIX_ROWS / 2 || !(present[row - first] & (1 << col))) {
        return 0;
    }
    return keys[row - first][col].stick;
}

// Learnt travel lives in the keyboard's EEPROM block after he_config_t, one value per matrix position of this half.
// Loaded from keyboard_post_init_kb, since QMK validates the EEPROM only after matrix_init_custom has run.
void he_travel_load(void) {
    uint16_t saved[MATRIX_ROWS / 2][MATRIX_COLS];
    eeconfig_read_kb_datablock(saved, HE_TRAVEL_OFFSET, sizeof(saved));
    for (uint8_t r = 0; r < MATRIX_ROWS / 2; r++) {
        for (uint8_t c = 0; c < MATRIX_COLS; c++) {
            keys[r][c].travel = saved[r][c] >= HE_MIN_TRAVEL && saved[r][c] <= 1023 ? saved[r][c] : 0;
        }
    }
}

// saves learnt travel at most every HE_TRAVEL_SAVE_MS, and only after a change, to spare the flash
void he_travel_task(void) {
    static uint32_t last = 0;
    if (!travel_dirty || timer_elapsed32(last) < HE_TRAVEL_SAVE_MS) {
        return;
    }
    uint16_t saved[MATRIX_ROWS / 2][MATRIX_COLS];
    for (uint8_t r = 0; r < MATRIX_ROWS / 2; r++) {
        for (uint8_t c = 0; c < MATRIX_COLS; c++) {
            saved[r][c] = keys[r][c].travel;
        }
    }
    eeconfig_update_kb_datablock(saved, HE_TRAVEL_OFFSET, sizeof(saved));
    travel_dirty = false;
    last         = timer_read32();
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
    he_config_task();
    he_travel_task();
    he_gamepad_task();
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
    he_config_task();
    he_travel_task();
    he_gamepad_task();
    housekeeping_task_user();
}
#endif
