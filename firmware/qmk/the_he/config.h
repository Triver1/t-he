#pragma once

#include "he_map.h"

// split link: one half-duplex wire over the TRRS, its pin set in he_map.h
// no handedness pin: flash with -bl uf2-split-left / uf2-split-right once per half
#define EE_HANDS
#define RP2040_BOOTLOADER_DOUBLE_TAP_RESET

// Actuation, as a share of each key's learned travel. Counts are 10-bit ADC readings.
#define HE_ACTUATION_PCT 45
#define HE_RELEASE_PCT 30
#define HE_MIN_ACTUATION 25          // floor, keeps sensor noise from triggering a key that has not moved yet
#define HE_DEFAULT_TRAVEL 150        // assumed until the key has been pressed once (Boardloaf-HE measures ~150)
#define HE_CALIBRATION_SAMPLES 32
#define HE_SETTLE_US 2               // after switching the mux, before the ADC samples

// self test: stuck-output limits for a sensor at rest; an SS49E-class part idles near VCC / 2 (~512)
#define HE_REST_LOW 150
#define HE_REST_HIGH 870
#define HE_REPORT_DELAY_MS 3000      // first report, once the host has had time to open the console
