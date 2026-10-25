#include QMK_KEYBOARD_H

// keys only feed the press report
bool process_record_user(uint16_t keycode, keyrecord_t *record) {
    return false;
}

// Key order per row: left half outer to inner, then right half inner to outer. The bottom row carries the
// outer keys at both ends; the thumbs run left to right.
const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
    [0] = LAYOUT(
                 KC_Q,    KC_W,    KC_E,    KC_R,    KC_T,        KC_Y,    KC_U,    KC_I,    KC_O,    KC_P,
                 KC_A,    KC_S,    KC_D,    KC_F,    KC_G,        KC_H,    KC_J,    KC_K,    KC_L,    KC_SCLN,
        KC_ESC,  KC_Z,    KC_X,    KC_C,    KC_V,    KC_B,        KC_N,    KC_M,    KC_COMM, KC_DOT,  KC_SLSH, KC_QUOT,
                                   KC_LGUI, MO(1),   KC_SPC,      KC_ENT,  MO(1),   KC_BSPC
    ),
    [1] = LAYOUT(
                 KC_1,    KC_2,    KC_3,    KC_4,    KC_5,        KC_6,    KC_7,    KC_8,    KC_9,    KC_0,
                 KC_TAB,  KC_LCTL, KC_LALT, KC_LSFT, KC_GRV,      KC_LEFT, KC_DOWN, KC_UP,   KC_RGHT, KC_MINS,
        QK_BOOT, KC_LBRC, KC_RBRC, KC_BSLS, KC_EQL,  KC_DEL,      KC_HOME, KC_PGDN, KC_PGUP, KC_END,  KC_CAPS, QK_BOOT,
                                   _______, _______, _______,     _______, _______, _______
    )
};
