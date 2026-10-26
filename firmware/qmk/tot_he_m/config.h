// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once

#include "he_map.h"

// split link: one half-duplex wire over the TRRS, its pin set in he_map.h
// no handedness pin: each half stores its side on first boot (the via_left / via_right images, INIT_EE_HANDS_*)
#define EE_HANDS
#define RP2040_BOOTLOADER_DOUBLE_TAP_RESET

// Key depth, in 0.1 mm. The scan turns each reading into a depth from a model of the magnet's field (he_matrix.c,
// depth_lut): the field grows with the cube of the magnet's closeness, so the reading barely moves in the first
// millimetre and races near the bottom. HE_GAP_DMM, the magnet-to-sensor distance with the key bottomed out, is an
// estimate: raise it if keys fire deeper than set, lower it if they fire shallower.
#define HE_TRAVEL_DMM 40             // total key travel, Gateron KS-20 class
#define HE_GAP_DMM 20
#define HE_ASSUMED_TRAVEL 350        // counts of full swing assumed until a key has learnt its own

// Bottom-out learning while typing (he_matrix.c, learn_travel)
#define HE_MIN_TRAVEL 150            // a press shallower than this many counts says nothing about the bottom
#define HE_BOTTOM_PCT 85             // a press reaching this share of the learnt travel counts as a bottom-out
#define HE_TRAVEL_SMOOTHING 4        // each bottom-out moves the travel this fraction (1/n) of the way to it
#define HE_LOW_STREAK 8              // this many short presses in a row replace the travel (a weaker magnet)...
#define HE_LOW_SPREAD_PCT 10         // ...if they all stop within this share of each other, as a real bottom does
#define HE_TRAVEL_SAVE_MS 60000      // learnt travel is written to EEPROM at most this often

// Defaults and VIA limits, in 0.1 mm. The live values are in he_config (he_config.c), stored in EEPROM.
#define HE_ACTUATION_DMM 20
#define HE_RELEASE_DMM 16
#define HE_ACTUATION_DMM_MIN 10      // shallower than about 1 mm the HE_MIN_ACTUATION noise floor takes over
#define HE_ACTUATION_DMM_MAX 38
#define HE_RELEASE_DMM_MIN 8         // HE_MIN_RELEASE counts, about 0.8 mm
#define HE_HYSTERESIS_DMM 2          // the release point stays at least this much shallower than the actuation point
#define HE_RAPID_TRIGGER 0           // rapid trigger off by default
#define HE_RT_DMM 3                  // rapid trigger press and release sensitivity
#define HE_RT_DMM_MIN 2              // below this, noise around the release point can retrigger a key
#define HE_RT_DMM_MAX 20
#define HE_STICK_DEADZONE_DMM 0      // controller layer: extra dead zone; 0 starts the stick at the first movement
#define HE_STICK_DEADZONE_DMM_MIN 0
#define HE_STICK_DEADZONE_DMM_MAX 20
#define HE_STICK_FULL_DMM 38         // controller layer: the stick is fully over at this depth, just short of bottom-out
#define HE_STICK_NOISE_MIN 2         // the resting noise measured at boot is taken as at least this many counts...
#define HE_STICK_NOISE_MAX 20        // ...and at most this many, for a key that was pressed during the measurement
#define HE_STICK_RANGE_DMM_MIN 5     // full deflection stays at least this much deeper than the dead zone
#define HE_GAMEPAD_LOOKUP_MS 250     // how often the controller layer looks up which keys carry the stick keycodes
#define EECONFIG_KB_DATA_SIZE 55     // he_config_t, then learnt travel for 3 x 8 matrix positions (he_config.h)
#define EECONFIG_KB_DATA_VERSION 6   // bump when the block's layout changes, so old contents are replaced by defaults

// controller layer: one gamepad with two axes (the stick) and buttons for JS_0 to JS_15
#define JOYSTICK_AXIS_COUNT 2
#define JOYSTICK_BUTTON_COUNT 16
#define SPLIT_TRANSACTION_IDS_KB RPC_ID_HE_CONFIG
#define HE_CONFIG_SYNC_MS 500        // how often the USB half sends the settings to the other half
// Noise floors, in counts of 10-bit ADC reading. They set the shallowest usable actuation, about 1 mm.
#define HE_MIN_ACTUATION 15          // a key that has moved less than this never fires, whatever its depth setting
#define HE_MIN_RELEASE 8             // a key that has moved less than this is always up
#define HE_GLITCH_COUNTS 40          // a scan where most keys moved this far at once is dropped as a glitch
#define HE_CALIBRATION_SAMPLES 32
#define HE_DEBOUNCE_SCANS 3          // a key changes state only after this many scans in a row agree
#define HE_SETTLE_US 10              // after switching the mux, before the ADC samples
#define HE_OVERSAMPLE 4              // conversions averaged per reading

// self test: stuck-output limits for a sensor at rest; an SS49E-class part idles near VCC / 2 (~512)
#define HE_REST_LOW 150
#define HE_REST_HIGH 870
#define HE_REPORT_DELAY_MS 3000      // first report, once the host has had time to open the console
