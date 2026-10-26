// SPDX-License-Identifier: GPL-2.0-or-later
// Runtime settings for the hall-effect scan: actuation and release depths, rapid trigger and the controller layer's
// stick, in 0.1 mm. Stored in
// the keyboard's EEPROM block, adjustable from VIA's custom menu (via_custom_value_command_kb), and sent from the USB
// half to the other half, since each half scans its own keys.
#pragma once

#include <stdint.h>

typedef struct {
    uint8_t actuation_dmm;
    uint8_t release_dmm;
    uint8_t rapid_trigger;  // 0 off, 1 on
    uint8_t rt_press_dmm;   // rapid trigger: how far a released key sinks before it fires again
    uint8_t rt_release_dmm; // rapid trigger: how far a pressed key rises before it lets go
    uint8_t stick_deadzone_dmm; // controller layer: depth a stick key must pass before the stick moves
    uint8_t stick_full_dmm;     // controller layer: depth at which the stick is fully over
} he_config_t;

#define HE_CONFIG_DEFAULTS                                                                                      \
    (he_config_t) {                                                                                            \
        .actuation_dmm = HE_ACTUATION_DMM, .release_dmm = HE_RELEASE_DMM, .rapid_trigger = HE_RAPID_TRIGGER, \
        .rt_press_dmm = HE_RT_DMM, .rt_release_dmm = HE_RT_DMM, .stick_deadzone_dmm = HE_STICK_DEADZONE_DMM,  \
        .stick_full_dmm = HE_STICK_FULL_DMM                                                                    \
    }

// learnt key travel (he_matrix.c) follows the settings in the same EEPROM block: one uint16_t per matrix position
#define HE_TRAVEL_OFFSET sizeof(he_config_t)
_Static_assert(HE_TRAVEL_OFFSET + sizeof(uint16_t) * MATRIX_ROWS / 2 * MATRIX_COLS <= EECONFIG_KB_DATA_SIZE,
               "settings and learnt travel do not fit the EEPROM block");

extern he_config_t he_config;

// VIA value ids on the custom channel, matching firmware/via/tot-he-m.json
enum he_via_value_id {
    id_he_actuation     = 1,
    id_he_release       = 2,
    id_he_rapid_trigger = 3,
    id_he_rt_press      = 4,
    id_he_rt_release    = 5,
    id_he_stick_deadzone = 6,
    id_he_stick_full     = 7,
    id_he_side           = 8,   // read-only, not in the VIA menu: 1 on the left half, 0 on the right, for flashing tools
};

void he_config_init(void);
void he_config_task(void);
void he_travel_load(void);   // he_matrix.c
void he_travel_task(void);   // he_matrix.c
uint16_t he_stick_depth(uint8_t row, uint8_t col); // he_matrix.c
void he_gamepad_task(void);  // he_gamepad.c
