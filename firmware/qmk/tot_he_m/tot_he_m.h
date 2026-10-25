// Tot-HE-m keyboard-level keycodes, included in every keymap through QMK_KEYBOARD_H.
#pragma once

#include "quantum.h"

// Controller layer (he_gamepad.c): keys with these keycodes drive the analog stick from how deep they are pressed.
// They stay in this order: VIA's customKeycodes in via/tot-he-m.json map onto QK_KB_0 upward.
enum tot_he_m_keycodes {
    STK_UP = QK_KB_0,
    STK_LEFT,
    STK_DOWN,
    STK_RGHT,
};

#define CONTROLLER_LAYER 4   // the default and via keymaps call it CTRL
