// SPDX-License-Identifier: GPL-2.0-or-later
// Controller layer: keys carrying the STK_* keycodes (tot_he_m.h) in the active layers drive an analog stick from how
// deep they are pressed, so a light press walks and a full press runs. Each axis is the depth of one key minus the
// opposite one; it starts at the first movement past the key's resting noise and is full at the full-deflection
// depth in he_config, with an optional extra dead zone. The stick runs on the USB half and
// reads keys on that half only; the other half's depths are not sent over the TRRS link.

#include "quantum.h"
#include "joystick.h"
#include "he_config.h"
#include "tot_he_m.h"

// matrix positions of the four stick keycodes in the active layers, refreshed by he_gamepad_find
static keypos_t stick_key[4];
static bool     stick_found[4];

// looks up which positions carry STK_* now; run on layer changes and every HE_GAMEPAD_LOOKUP_MS, since VIA can
// remap keys at any time
static void he_gamepad_find(void) {
    for (uint8_t i = 0; i < 4; i++) {
        stick_found[i] = false;
    }
    for (uint8_t row = 0; row < MATRIX_ROWS; row++) {
        for (uint8_t col = 0; col < MATRIX_COLS; col++) {
            keypos_t key = {.row = row, .col = col};
            uint16_t kc  = keymap_key_to_keycode(layer_switch_get_layer(key), key);
            if (kc >= STK_UP && kc <= STK_RGHT) {
                stick_key[kc - STK_UP]   = key;
                stick_found[kc - STK_UP] = true;
            }
        }
    }
}

// 0 to JOYSTICK_MAX_VALUE from one key's depth: from the first movement (plus any dead zone) to the full-deflection
// depth
static int16_t he_gamepad_amount(uint8_t i) {
    if (!stick_found[i]) {
        return 0;
    }
    int32_t pos  = he_stick_depth(stick_key[i].row, stick_key[i].col);
    int32_t dead = he_config.stick_deadzone_dmm * 10, full = he_config.stick_full_dmm * 10;
    if (pos <= dead) {
        return 0;
    }
    return pos >= full ? JOYSTICK_MAX_VALUE : (pos - dead) * JOYSTICK_MAX_VALUE / (full - dead);
}

layer_state_t layer_state_set_kb(layer_state_t state) {
    state = layer_state_set_user(state);
    he_gamepad_find();
    return state;
}

void he_gamepad_task(void) {
    static uint32_t last_lookup = 0;
    static int16_t  last_x = 0, last_y = 0;
    if (!is_keyboard_master()) {
        return;
    }
    if (timer_elapsed32(last_lookup) >= HE_GAMEPAD_LOOKUP_MS) {
        last_lookup = timer_read32();
        he_gamepad_find();
    }
    // HID axes: x grows to the right, y grows downwards
    int16_t x = he_gamepad_amount(STK_RGHT - STK_UP) - he_gamepad_amount(STK_LEFT - STK_UP);
    int16_t y = he_gamepad_amount(STK_DOWN - STK_UP) - he_gamepad_amount(STK_UP - STK_UP);
    if (x != last_x || y != last_y) {
        joystick_set_axis(0, x);
        joystick_set_axis(1, y);
        last_x = x;
        last_y = y;
    }
}

// the stick keycodes only feed the axes, they never type
bool process_record_kb(uint16_t keycode, keyrecord_t *record) {
    if (keycode >= STK_UP && keycode <= STK_RGHT) {
        return false;
    }
    return process_record_user(keycode, record);
}
